from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.mixins import TenantQuerysetMixin
from apps.emissions.models import AnomalyFlag, EmissionRecord
from apps.emissions.serializers import (
    EmissionRecordSerializer,
    EmissionRecordUpdateSerializer,
    HistoryRecordSerializer,
    ReviewNoteSerializer,
)
from apps.ingestion.models import IngestionJob
from apps.reviews.models import ReviewAction
from apps.reviews.services import (
    approve_record,
    bulk_approve_job,
    edit_record,
    lock_record,
    reject_record,
)


class EmissionRecordListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = EmissionRecordSerializer

    def get_queryset(self):
        qs = EmissionRecord.objects.select_related(
            "ingestion_job", "reviewed_by"
        ).prefetch_related("anomaly_flags")

        params = self.request.query_params
        if job_id := params.get("ingestion_job"):
            qs = qs.filter(ingestion_job_id=job_id)
        if source_type := params.get("source_type"):
            qs = qs.filter(source_type=source_type)
        if scope := params.get("scope"):
            qs = qs.filter(scope=scope)
        if review_status := params.get("review_status"):
            qs = qs.filter(review_status=review_status)
        if activity_after := params.get("activity_date_after"):
            qs = qs.filter(activity_date__gte=activity_after)
        if activity_before := params.get("activity_date_before"):
            qs = qs.filter(activity_date__lte=activity_before)
        if has_anomaly := params.get("has_anomaly"):
            if has_anomaly.lower() == "true":
                qs = qs.filter(anomaly_flags__isnull=False).distinct()
        return qs


class EmissionRecordDetailView(TenantQuerysetMixin, generics.RetrieveUpdateAPIView):
    serializer_class = EmissionRecordSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return EmissionRecord.objects.prefetch_related("anomaly_flags")

    def patch(self, request, *args, **kwargs):
        record = self.get_object()
        ser = EmissionRecordUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        edit_record(
            record,
            request.user,
            raw_value=ser.validated_data.get("raw_value"),
            raw_unit=ser.validated_data.get("raw_unit"),
            note=ser.validated_data.get("note", ""),
        )
        return Response(EmissionRecordSerializer(record).data)


class JobEmissionRecordsView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = EmissionRecordSerializer

    def get_queryset(self):
        job = get_object_or_404(
            IngestionJob,
            pk=self.kwargs["pk"],
            tenant=self.get_tenant(),
        )
        return EmissionRecord.objects.filter(
            ingestion_job=job,
        ).prefetch_related("anomaly_flags")


class RecordApproveView(TenantQuerysetMixin, APIView):
    def post(self, request, pk):
        record = get_object_or_404(
            EmissionRecord, pk=pk, tenant=self.get_tenant()
        )
        ser = ReviewNoteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        approve_record(record, request.user, ser.validated_data.get("note", ""))
        return Response(EmissionRecordSerializer(record).data)


class RecordRejectView(TenantQuerysetMixin, APIView):
    def post(self, request, pk):
        record = get_object_or_404(
            EmissionRecord, pk=pk, tenant=self.get_tenant()
        )
        ser = ReviewNoteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        reject_record(record, request.user, ser.validated_data.get("note", ""))
        return Response(EmissionRecordSerializer(record).data)


class RecordLockView(TenantQuerysetMixin, APIView):
    def post(self, request, pk):
        record = get_object_or_404(
            EmissionRecord, pk=pk, tenant=self.get_tenant()
        )
        ser = ReviewNoteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        lock_record(record, request.user, ser.validated_data.get("note", ""))
        return Response(EmissionRecordSerializer(record).data)


class RecordHistoryView(TenantQuerysetMixin, APIView):
    def get(self, request, pk):
        record = get_object_or_404(
            EmissionRecord, pk=pk, tenant=self.get_tenant()
        )
        entries = []
        for h in record.history.all().order_by("-history_date"):
            entries.append({
                "history_id": h.history_id,
                "history_date": h.history_date,
                "history_type": h.history_type,
                "history_user": str(h.history_user) if h.history_user else None,
                "raw_value": str(h.raw_value),
                "raw_unit": h.raw_unit,
                "normalized_value_kg": str(h.normalized_value_kg),
                "review_status": h.review_status,
                "is_edited": h.is_edited,
            })
        return Response(HistoryRecordSerializer(entries, many=True).data)


class JobBulkApproveView(TenantQuerysetMixin, APIView):
    def post(self, request, pk):
        job = get_object_or_404(
            IngestionJob, pk=pk, tenant=self.get_tenant()
        )
        count = bulk_approve_job(job, request.user)
        return Response({"approved_count": count})


class AnomalyListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = None

    def list(self, request, *args, **kwargs):
        tenant = self.get_tenant()
        qs = AnomalyFlag.objects.filter(tenant=tenant)

        if scope := request.query_params.get("scope"):
            qs = qs.filter(emission_record__scope=scope)
        if source_type := request.query_params.get("source_type"):
            qs = qs.filter(emission_record__source_type=source_type)
        if date_after := request.query_params.get("activity_date_after"):
            qs = qs.filter(emission_record__activity_date__gte=date_after)
        if date_before := request.query_params.get("activity_date_before"):
            qs = qs.filter(emission_record__activity_date__lte=date_before)

        grouped = (
            qs.values("flag_type", "severity")
            .annotate(
                count=Count("id"),
                affected_jobs=Count("emission_record__ingestion_job", distinct=True),
            )
            .order_by("-count")
        )
        return Response(list(grouped))


class DashboardSummaryView(TenantQuerysetMixin, APIView):
    def get(self, request):
        tenant = self.get_tenant()
        records = EmissionRecord.objects.filter(tenant=tenant)

        summary = {
            "total_records": records.count(),
            "total_kgco2e": records.aggregate(s=Sum("normalized_value_kg"))["s"] or 0,
            "by_scope": list(
                records.values("scope")
                .annotate(count=Count("id"), kg=Sum("normalized_value_kg"))
                .order_by("scope")
            ),
            "by_review_status": list(
                records.values("review_status")
                .annotate(count=Count("id"))
                .order_by("review_status")
            ),
            "pending_review": records.filter(
                review_status=EmissionRecord.ReviewStatus.PENDING
            ).count(),
            "open_anomalies": AnomalyFlag.objects.filter(tenant=tenant).count(),
            "recent_jobs": IngestionJob.objects.filter(tenant=tenant).order_by(
                "-created_at"
            )[:5].values(
                "id", "source_category", "status", "rows_created", "created_at"
            ),
        }
        return Response(summary)
