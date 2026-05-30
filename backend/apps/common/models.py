"""Shared model abstractions for multi-tenant isolation."""
from django.db import models


class TenantModel(models.Model):
    """Abstract base: every business table carries a tenant FK."""

    tenant = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
    )

    class Meta:
        abstract = True
