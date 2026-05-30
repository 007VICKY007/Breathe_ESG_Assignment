import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Organization(models.Model):
    """Tenant boundary — all data rows belong to exactly one organization."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Platform user scoped to a single organization."""

    class Role(models.TextChoices):
        ANALYST = "ANALYST", "Analyst"
        ADMIN = "ADMIN", "Admin"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="users",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ANALYST,
    )

    class Meta:
        ordering = ["username"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "email"],
                name="unique_email_per_org",
                condition=models.Q(email__gt=""),
            ),
        ]

    def __str__(self):
        return f"{self.username} ({self.organization.slug})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
