from rest_framework import serializers

from apps.ingestion.models import IngestionJob


class IngestionJobSerializer(serializers.ModelSerializer):
    error_count = serializers.SerializerMethodField()

    class Meta:
        model = IngestionJob
        fields = (
            "id",
            "source_category",
            "original_filename",
            "status",
            "rows_total",
            "rows_created",
            "rows_skipped_duplicate",
            "rows_failed",
            "error_count",
            "error_log",
            "started_at",
            "completed_at",
            "created_at",
        )
        read_only_fields = fields

    def get_error_count(self, obj):
        return len(obj.error_log or [])


class IngestionJobDetailSerializer(IngestionJobSerializer):
    pending_review_count = serializers.SerializerMethodField()
    anomaly_count = serializers.SerializerMethodField()

    class Meta(IngestionJobSerializer.Meta):
        fields = IngestionJobSerializer.Meta.fields + (
            "pending_review_count",
            "anomaly_count",
        )

    def get_pending_review_count(self, obj):
        return obj.emission_records.filter(
            review_status="PENDING",
        ).count()

    def get_anomaly_count(self, obj):
        from apps.emissions.models import AnomalyFlag
        return AnomalyFlag.objects.filter(
            emission_record__ingestion_job=obj,
        ).count()


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
