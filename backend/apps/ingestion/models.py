import uuid

from django.db import models

from apps.common.models import TenantModel


class IngestionJob(TenantModel):
    """
    One record per file upload or API pull.
    Tracks async pipeline status — parsers attach in Phase 2.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        DONE = "DONE", "Done"
        FAILED = "FAILED", "Failed"

    class SourceCategory(models.TextChoices):
        SAP = "SAP", "SAP flat file"
        UTILITY = "UTILITY", "Utility CSV"
        TRAVEL = "TRAVEL", "Travel CSV"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_category = models.CharField(max_length=20, choices=SourceCategory.choices)
    original_filename = models.CharField(max_length=512)
    raw_file = models.FileField(upload_to="ingestion/%Y/%m/%d/")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    rows_total = models.PositiveIntegerField(default=0)
    rows_created = models.PositiveIntegerField(default=0)
    rows_skipped_duplicate = models.PositiveIntegerField(default=0)
    rows_failed = models.PositiveIntegerField(default=0)
    error_log = models.JSONField(default=list, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        "organizations.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="ingestion_jobs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "created_at"]),
        ]

    def __str__(self):
        return f"{self.original_filename} [{self.status}]"


class DataSource(TenantModel):
    """Per-org configuration for a connected data source type."""

    class SourceType(models.TextChoices):
        SAP = "SAP", "SAP"
        UTILITY = "UTILITY", "Utility"
        TRAVEL = "TRAVEL", "Travel"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    display_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("tenant", "source_type", "display_name")]
        ordering = ["source_type", "display_name"]

    def __str__(self):
        return f"{self.display_name} ({self.source_type})"
