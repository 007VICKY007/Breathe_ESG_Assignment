import logging

from django.conf import settings
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.mixins import TenantQuerysetMixin
from apps.ingestion.models import IngestionJob
from apps.ingestion.serializers import (
    FileUploadSerializer,
    IngestionJobDetailSerializer,
    IngestionJobSerializer,
)
from apps.ingestion.tasks import process_ingestion_job

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

        if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
            process_ingestion_job(str(job.id))
            job.refresh_from_db()
        else:
            process_ingestion_job.delay(str(job.id))

        return Response(
            IngestionJobSerializer(job).data,
            status=status.HTTP_202_ACCEPTED,
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


class IngestionJobDetailView(TenantQuerysetMixin, generics.RetrieveAPIView):
    serializer_class = IngestionJobDetailSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return IngestionJob.objects.all()
