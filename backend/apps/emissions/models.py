import uuid

from django.db import models
from simple_history.models import HistoricalRecords

from apps.common.models import TenantModel


class EmissionRecord(TenantModel):
    """
    Canonical normalized emission row.
    Factors and normalized kgCO2e are frozen at ingestion time.
    """

    class SourceType(models.TextChoices):
        SAP_FUEL = "SAP_FUEL", "SAP fuel"
        SAP_PROCUREMENT = "SAP_PROCUREMENT", "SAP procurement"
        UTILITY_ELECTRICITY = "UTILITY_ELECTRICITY", "Utility electricity"
        TRAVEL_FLIGHT = "TRAVEL_FLIGHT", "Travel flight"
        TRAVEL_HOTEL = "TRAVEL_HOTEL", "Travel hotel"
        TRAVEL_GROUND = "TRAVEL_GROUND", "Travel ground"

    class Scope(models.IntegerChoices):
        SCOPE_1 = 1, "Scope 1"
        SCOPE_2 = 2, "Scope 2"
        SCOPE_3 = 3, "Scope 3"

    class ReviewStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        LOCKED = "LOCKED", "Locked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ingestion_job = models.ForeignKey(
        "ingestion.IngestionJob",
        on_delete=models.CASCADE,
        related_name="emission_records",
    )
    source_type = models.CharField(max_length=32, choices=SourceType.choices)
    scope = models.PositiveSmallIntegerField(choices=Scope.choices)

    activity_date = models.DateField(
        help_text="Date the emission activity occurred (not ingestion date).",
    )
    period_start = models.DateField(
        null=True,
        blank=True,
        help_text="Billing / reporting period start (utilities).",
    )
    period_end = models.DateField(
        null=True,
        blank=True,
        help_text="Billing / reporting period end (utilities).",
    )

    raw_value = models.DecimalField(max_digits=20, decimal_places=6)
    raw_unit = models.CharField(max_length=32)
    normalized_value_kg = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        help_text="Always kgCO2e after unit + factor normalization.",
    )
    emission_factor_used = models.DecimalField(max_digits=20, decimal_places=8)
    emission_factor_source = models.CharField(max_length=128)

    location = models.CharField(
        max_length=512,
        blank=True,
        help_text="Plant code, meter address, or airport pair.",
    )
    vendor_or_carrier = models.CharField(max_length=255, blank=True)

    source_row_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 of raw source row for idempotent deduplication.",
    )
    is_edited = models.BooleanField(
        default=False,
        help_text="True if an analyst modified values post-ingestion.",
    )

    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        "organizations.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_emissions",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ["-activity_date", "-created_at"]
        indexes = [
            models.Index(fields=["tenant", "review_status"]),
            models.Index(fields=["tenant", "source_type"]),
            models.Index(fields=["tenant", "scope"]),
            models.Index(fields=["tenant", "activity_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "source_row_hash"],
                name="unique_emission_per_tenant_hash",
            ),
        ]

    def __str__(self):
        return f"{self.source_type} {self.activity_date} ({self.normalized_value_kg} kgCO2e)"


class AnomalyFlag(TenantModel):
    """System-detected issue on an emission record."""

    class Severity(models.TextChoices):
        ERROR = "ERROR", "Error"
        WARNING = "WARNING", "Warning"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emission_record = models.ForeignKey(
        EmissionRecord,
        on_delete=models.CASCADE,
        related_name="anomaly_flags",
    )
    flag_type = models.CharField(max_length=64, db_index=True)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    message = models.TextField()
    affected_field = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "flag_type"]),
            models.Index(fields=["tenant", "severity"]),
        ]

    def __str__(self):
        return f"{self.flag_type} [{self.severity}]"
