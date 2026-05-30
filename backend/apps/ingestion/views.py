import logging

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.mixins import TenantQuerysetMixin
from apps.emissions.models import EmissionRecord
from apps.ingestion.models import IngestionJob
from apps.ingestion.serializers import (
    FileUploadSerializer,
    IngestionJobDetailSerializer,
    IngestionJobSerializer,
)
from apps.ingestion.tasks import dispatch_ingestion_job, run_ingestion_job_sync

logger = logging.getLogger(__name__)


class BaseIngestView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    source_category = None

    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded = serializer.validated_data["file"]

        job = IngestionJob.objects.create(
            tenant=request.user.organization,
            source_category=self.source_category,
            original_filename=uploaded.name,
            raw_file=uploaded,
            created_by=request.user,
            status=IngestionJob.Status.PENDING,
        )

        dispatch_ingestion_job(str(job.id))
        job.refresh_from_db()

        http_status = (
            status.HTTP_200_OK
            if job.status in (IngestionJob.Status.DONE, IngestionJob.Status.FAILED)
            else status.HTTP_202_ACCEPTED
        )

        return Response(
            IngestionJobSerializer(job).data,
            status=http_status,
        )


class IngestSapView(BaseIngestView):
    source_category = IngestionJob.SourceCategory.SAP


class IngestUtilityView(BaseIngestView):
    source_category = IngestionJob.SourceCategory.UTILITY


class IngestTravelView(BaseIngestView):
    source_category = IngestionJob.SourceCategory.TRAVEL


class IngestionJobListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = IngestionJobSerializer

    def get_queryset(self):
        return IngestionJob.objects.all()


class IngestionJobDetailView(TenantQuerysetMixin, generics.RetrieveDestroyAPIView):
    serializer_class = IngestionJobDetailSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return IngestionJob.objects.all()

    def perform_destroy(self, instance):
        locked = EmissionRecord.objects.filter(
            ingestion_job=instance,
            review_status=EmissionRecord.ReviewStatus.LOCKED,
        ).exists()
        if locked:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                "Cannot delete job with audit-locked records. Unlock records first."
            )

        if instance.raw_file:
            instance.raw_file.delete(save=False)
        logger.info("Deleting ingestion job %s for tenant %s", instance.id, instance.tenant_id)
        instance.delete()


class IngestionJobRetryView(TenantQuerysetMixin, APIView):
    """Re-run a stuck PENDING/FAILED job synchronously."""

    def post(self, request, pk):
        job = get_object_or_404(
            IngestionJob,
            pk=pk,
            tenant=self.get_tenant(),
        )
        if job.status == IngestionJob.Status.PROCESSING:
            return Response(
                {"error": "JobBusy", "detail": "Job is currently processing."},
                status=status.HTTP_409_CONFLICT,
            )

        job.status = IngestionJob.Status.PENDING
        job.error_log = []
        job.rows_created = 0
        job.rows_failed = 0
        job.rows_skipped_duplicate = 0
        job.save()

        run_ingestion_job_sync(str(job.id))
        job.refresh_from_db()
        return Response(IngestionJobSerializer(job).data)
