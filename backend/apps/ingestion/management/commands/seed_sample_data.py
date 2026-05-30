"""
Load sample CSVs from repo sample_data/ for demo ingestion.
Usage: python manage.py seed_sample_data --username admin@demo.com
"""
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.ingestion.models import IngestionJob
from apps.ingestion.tasks import process_ingestion_job

User = get_user_model()
SAMPLE_DIR = Path(__file__).resolve().parents[5] / "sample_data"


class Command(BaseCommand):
    help = "Ingest sample SAP, utility, and travel files for a user"

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)

    def handle(self, *args, **options):
        user = User.objects.get(username=options["username"])
        files = [
            (IngestionJob.SourceCategory.SAP, "sap_me2m_export.csv"),
            (IngestionJob.SourceCategory.UTILITY, "utility_meter_export.csv"),
            (IngestionJob.SourceCategory.TRAVEL, "travel_concur_export.csv"),
        ]
        for category, name in files:
            path = SAMPLE_DIR / name
            if not path.exists():
                self.stderr.write(f"Missing {path}")
                continue
            from django.core.files import File

            with path.open("rb") as fh:
                job = IngestionJob.objects.create(
                    tenant=user.organization,
                    source_category=category,
                    original_filename=name,
                    raw_file=File(fh, name=name),
                    created_by=user,
                )
            process_ingestion_job(str(job.id))
            job.refresh_from_db()
            self.stdout.write(
                self.style.SUCCESS(
                    f"{name}: {job.status} — {job.rows_created} created, "
                    f"{job.rows_skipped_duplicate} dupes"
                )
            )
