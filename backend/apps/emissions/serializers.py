from rest_framework import serializers

from apps.emissions.models import AnomalyFlag, EmissionRecord


class AnomalyFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnomalyFlag
        fields = (
            "id",
            "flag_type",
            "severity",
            "message",
            "affected_field",
            "created_at",
        )


class EmissionRecordSerializer(serializers.ModelSerializer):
    anomaly_flags = AnomalyFlagSerializer(many=True, read_only=True)
    has_error_flags = serializers.SerializerMethodField()

    class Meta:
        model = EmissionRecord
        fields = (
            "id",
            "ingestion_job",
            "source_type",
            "scope",
            "activity_date",
            "period_start",
            "period_end",
            "raw_value",
            "raw_unit",
            "normalized_value_kg",
            "emission_factor_used",
            "emission_factor_source",
            "location",
            "vendor_or_carrier",
            "source_row_hash",
            "is_edited",
            "review_status",
            "reviewed_by",
            "reviewed_at",
            "anomaly_flags",
            "has_error_flags",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "ingestion_job",
            "source_type",
            "scope",
            "activity_date",
            "period_start",
            "period_end",
            "source_row_hash",
            "emission_factor_used",
            "emission_factor_source",
            "location",
            "vendor_or_carrier",
            "created_at",
            "updated_at",
        )

    def get_has_error_flags(self, obj):
        return obj.anomaly_flags.filter(severity=AnomalyFlag.Severity.ERROR).exists()


class EmissionRecordUpdateSerializer(serializers.Serializer):
    raw_value = serializers.DecimalField(max_digits=20, decimal_places=6, required=False)
    raw_unit = serializers.CharField(max_length=32, required=False)
    note = serializers.CharField(required=False, allow_blank=True, default="")


class ReviewNoteSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, default="")


class HistoryRecordSerializer(serializers.Serializer):
    history_id = serializers.IntegerField()
    history_date = serializers.DateTimeField()
    history_type = serializers.CharField()
    history_user = serializers.CharField(allow_null=True)
    raw_value = serializers.CharField()
    raw_unit = serializers.CharField()
    normalized_value_kg = serializers.CharField()
    review_status = serializers.CharField()
    is_edited = serializers.BooleanField()
