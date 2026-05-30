from rest_framework import serializers

from apps.reviews.models import ReviewAction


class ReviewActionSerializer(serializers.ModelSerializer):
    performed_by_username = serializers.CharField(
        source="performed_by.username", read_only=True, default=None
    )
    emission_record_id = serializers.UUIDField(source="emission_record.id")

    class Meta:
        model = ReviewAction
        fields = (
            "id",
            "emission_record_id",
            "action",
            "performed_by_username",
            "note",
            "previous_values",
            "new_values",
            "created_at",
        )
