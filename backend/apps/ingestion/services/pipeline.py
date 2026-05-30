"""
Ingestion pipeline: parse → validate → normalize → dedup → flag → persist.
Idempotent on source_row_hash per tenant.
"""
import logging
from typing import Callable

from django.db import transaction
from django.utils import timezone

from apps.emissions.models import AnomalyFlag, EmissionRecord
from apps.ingestion.models import IngestionJob
from apps.ingestion.parsers.base import ParseResult, ParsedEmissionRow
from apps.ingestion.services.anomalies import build_anomaly_objects

logger = logging.getLogger(__name__)


def run_ingestion_pipeline(
    job: IngestionJob,
    parse_fn: Callable[[bytes, str], ParseResult],
) -> IngestionJob:
    """Execute full pipeline for one IngestionJob. Safe to retry (hash dedup)."""
    job.status = IngestionJob.Status.PROCESSING
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at", "updated_at"])

    error_log: list[dict] = []
    rows_created = 0
    rows_skipped = 0
    rows_failed = 0

    try:
        with job.raw_file.open("rb") as fh:
            content = fh.read()
        parse_result = parse_fn(content, job.original_filename)
        job.rows_total = len(parse_result.records) + len(parse_result.errors)
        error_log.extend(parse_result.errors)

        existing_hashes = set(
            EmissionRecord.objects.filter(tenant=job.tenant).values_list(
                "source_row_hash", flat=True
            )
        )

        for parsed in parse_result.records:
            if parsed.source_row_hash in existing_hashes:
                rows_skipped += 1
                continue

            try:
                with transaction.atomic():
                    record = EmissionRecord.objects.create(
                        tenant=job.tenant,
                        ingestion_job=job,
                        source_type=parsed.source_type,
                        scope=parsed.scope,
                        activity_date=parsed.activity_date,
                        period_start=parsed.period_start,
                        period_end=parsed.period_end,
                        raw_value=parsed.raw_value,
                        raw_unit=parsed.raw_unit,
                        normalized_value_kg=parsed.normalized_value_kg,
                        emission_factor_used=parsed.emission_factor_used,
                        emission_factor_source=parsed.emission_factor_source,
                        location=parsed.location,
                        vendor_or_carrier=parsed.vendor_or_carrier,
                        source_row_hash=parsed.source_row_hash,
                    )
                    flags = build_anomaly_objects(
                        job.tenant_id, record, parsed.anomalies
                    )
                    if flags:
                        AnomalyFlag.objects.bulk_create(flags)

                    existing_hashes.add(parsed.source_row_hash)
                    rows_created += 1
            except Exception as exc:
                logger.exception("Failed to persist row %s", parsed.row_number)
                rows_failed += 1
                error_log.append({
                    "row": parsed.row_number,
                    "message": str(exc),
                })

        job.rows_created = rows_created
        job.rows_skipped_duplicate = rows_skipped
        job.rows_failed = rows_failed + len(parse_result.errors)
        job.error_log = error_log
        job.status = IngestionJob.Status.DONE
        job.completed_at = timezone.now()
        job.save()

    except Exception as exc:
        logger.exception("Ingestion job %s failed", job.id)
        job.status = IngestionJob.Status.FAILED
        job.error_log = error_log + [{"row": 0, "message": str(exc)}]
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error_log", "completed_at", "updated_at"])
        raise

    return job
