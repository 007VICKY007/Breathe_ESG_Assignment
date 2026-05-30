import uuid

from django.db import models

from apps.common.models import TenantModel


class ReviewAction(TenantModel):
    """Append-only log of analyst decisions (complements django-simple-history on values)."""

    class Action(models.TextChoices):
        APPROVE = "APPROVE", "Approve"
        REJECT = "REJECT", "Reject"
        EDIT = "EDIT", "Edit"
        LOCK = "LOCK", "Lock"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emission_record = models.ForeignKey(
        "emissions.EmissionRecord",
        on_delete=models.CASCADE,
        related_name="review_actions",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    performed_by = models.ForeignKey(
        "organizations.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="review_actions",
    )
    note = models.TextField(blank=True)
    previous_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["tenant", "action"]),
        ]

    def __str__(self):
        return f"{self.action} on {self.emission_record_id}"
