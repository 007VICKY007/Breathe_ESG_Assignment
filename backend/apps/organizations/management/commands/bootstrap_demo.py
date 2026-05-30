"""
Bootstrap demo organization and admin user for deployed prototype.
Idempotent — safe to run on every deploy.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.organizations.models import Organization

User = get_user_model()

DEMO_ORG_SLUG = "breathe-demo"
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo12345"
DEMO_EMAIL = "demo@breatheesg.com"


class Command(BaseCommand):
    help = "Create demo org + analyst user for evaluators (idempotent)"

    def handle(self, *args, **options):
        org, created = Organization.objects.get_or_create(
            slug=DEMO_ORG_SLUG,
            defaults={"name": "Breathe ESG Demo Corp"},
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created organization {org.name}"))

        user, user_created = User.objects.get_or_create(
            username=DEMO_USERNAME,
            defaults={
                "email": DEMO_EMAIL,
                "organization": org,
                "role": User.Role.ADMIN,
            },
        )
        if user_created:
            user.set_password(DEMO_PASSWORD)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Demo user created: {DEMO_USERNAME} / {DEMO_PASSWORD}"
                )
            )
        else:
            self.stdout.write(f"Demo user already exists: {DEMO_USERNAME}")
