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


@shared_task(bind=True, max_retries=2)
def process_ingestion_job(self, job_id: str):
    """Celery task — idempotent via source_row_hash dedup in pipeline."""
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
        job.save()
        return "FAILED"

    try:
        run_ingestion_pipeline(job, parse_fn)
    except Exception:
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30)
        raise
    return job.status
