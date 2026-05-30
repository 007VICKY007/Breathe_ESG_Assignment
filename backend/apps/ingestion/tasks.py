import logging

from celery import shared_task

from apps.ingestion.models import IngestionJob
from apps.ingestion.parsers import parse_sap_file, parse_travel_file, parse_utility_file
from apps.ingestion.services.pipeline import run_ingestion_pipeline

logger = logging.getLogger(__name__)

PARSERS = {
    IngestionJob.SourceCategory.SAP: parse_sap_file,
    IngestionJob.SourceCategory.UTILITY: parse_utility_file,
    IngestionJob.SourceCategory.TRAVEL: parse_travel_file,
}


def _resolve_parser(job: IngestionJob):
    if job.source_category == IngestionJob.SourceCategory.UTILITY:
        from apps.emissions.models import EmissionRecord

        historical = [
            float(v)
            for v in EmissionRecord.objects.filter(
                tenant=job.tenant,
                source_type=EmissionRecord.SourceType.UTILITY_ELECTRICITY,
            ).values_list("raw_value", flat=True)
        ]

        def parse_with_history(content, filename):
            return parse_utility_file(content, filename, historical_kwh=historical)

        return parse_with_history
    return PARSERS.get(job.source_category)


def run_ingestion_job_sync(job_id: str) -> str:
    """
    Run ingestion in-process (no Celery).
    Used when worker is unavailable or INGESTION_RUN_SYNC=True.
    """
    job = IngestionJob.objects.select_related("tenant").get(pk=job_id)
    if job.status not in (
        IngestionJob.Status.PENDING,
        IngestionJob.Status.PROCESSING,
    ):
        logger.info("Job %s already terminal (%s), skipping", job_id, job.status)
        return str(job.status)

    parse_fn = _resolve_parser(job)
    if not parse_fn:
        job.status = IngestionJob.Status.FAILED
        job.error_log = [{"row": 0, "message": f"Unknown source {job.source_category}"}]
        job.save(update_fields=["status", "error_log", "updated_at"])
        return "FAILED"

    run_ingestion_pipeline(job, parse_fn)
    job.refresh_from_db()
    return job.status


def dispatch_ingestion_job(job_id: str) -> None:
    """Queue via Celery or run synchronously depending on settings."""
    from django.conf import settings

    run_sync = getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False) or getattr(
        settings, "INGESTION_RUN_SYNC", True
    )

    if run_sync:
        logger.info("Running ingestion job %s synchronously", job_id)
        run_ingestion_job_sync(job_id)
        return

    try:
        process_ingestion_job.delay(job_id)
        logger.info("Dispatched ingestion job %s to Celery", job_id)
    except Exception:
        logger.exception(
            "Celery dispatch failed for job %s — falling back to sync", job_id
        )
        run_ingestion_job_sync(job_id)


@shared_task(bind=True, max_retries=2)
def process_ingestion_job(self, job_id: str):
    """Celery task — idempotent via source_row_hash dedup in pipeline."""
    try:
        return run_ingestion_job_sync(job_id)
    except Exception:
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30)
        raise
