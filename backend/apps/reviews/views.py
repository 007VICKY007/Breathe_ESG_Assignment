from rest_framework import generics

from apps.common.mixins import TenantQuerysetMixin
from apps.reviews.models import ReviewAction
from apps.reviews.serializers import ReviewActionSerializer


class AuditLogListView(TenantQuerysetMixin, generics.ListAPIView):
    """Append-only chronological review actions for the tenant."""

    serializer_class = ReviewActionSerializer

    def get_queryset(self):
        return ReviewAction.objects.select_related(
            "performed_by", "emission_record"
        ).order_by("-created_at")
