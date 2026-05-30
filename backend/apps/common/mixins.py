"""DRF queryset mixins — tenant isolation at the ORM layer, not in views."""
from rest_framework.exceptions import PermissionDenied


class TenantQuerysetMixin:
    """Filter querysets to the authenticated user's organization."""

    tenant_field = "tenant"

    def get_tenant(self):
        user = self.request.user
        if not user.is_authenticated:
            return None
        if not hasattr(user, "organization") or user.organization_id is None:
            raise PermissionDenied("User is not assigned to an organization.")
        return user.organization

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = self.get_tenant()
        if tenant is not None:
            qs = qs.filter(**{self.tenant_field: tenant})
        return qs
