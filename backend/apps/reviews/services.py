"""Analyst review workflow — approve, reject, edit, lock."""
import logging
from decimal import Decimal

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.emissions.models import AnomalyFlag, EmissionRecord
from apps.reviews.models import ReviewAction

logger = logging.getLogger(__name__)


def _snapshot(record: EmissionRecord) -> dict:
    return {
        "raw_value": str(record.raw_value),
        "raw_unit": record.raw_unit,
        "normalized_value_kg": str(record.normalized_value_kg),
        "review_status": record.review_status,
    }


def _log_action(record, user, action, note="", previous=None, new=None):
    ReviewAction.objects.create(
        tenant=record.tenant,
        emission_record=record,
        action=action,
        performed_by=user,
        note=note,
        previous_values=previous or {},
        new_values=new or {},
    )


def approve_record(record: EmissionRecord, user, note="") -> EmissionRecord:
    if record.review_status == EmissionRecord.ReviewStatus.LOCKED:
        raise ValidationError("Locked records cannot be approved.")
    if record.anomaly_flags.filter(severity=AnomalyFlag.Severity.ERROR).exists():
        raise ValidationError("Cannot approve rows with ERROR-level anomaly flags.")

    previous = _snapshot(record)
    record.review_status = EmissionRecord.ReviewStatus.APPROVED
    record.reviewed_by = user
    record.reviewed_at = timezone.now()
    record.save()
    _log_action(record, user, ReviewAction.Action.APPROVE, note, previous, _snapshot(record))
    return record


def reject_record(record: EmissionRecord, user, note="") -> EmissionRecord:
    if record.review_status == EmissionRecord.ReviewStatus.LOCKED:
        raise ValidationError("Locked records cannot be rejected.")

    previous = _snapshot(record)
    record.review_status = EmissionRecord.ReviewStatus.REJECTED
    record.reviewed_by = user
    record.reviewed_at = timezone.now()
    record.save()
    _log_action(record, user, ReviewAction.Action.REJECT, note, previous, _snapshot(record))
    return record


def lock_record(record: EmissionRecord, user, note="") -> EmissionRecord:
    if record.review_status != EmissionRecord.ReviewStatus.APPROVED:
        raise ValidationError("Only approved records can be locked for audit.")

    previous = _snapshot(record)
    record.review_status = EmissionRecord.ReviewStatus.LOCKED
    record.reviewed_by = user
    record.reviewed_at = timezone.now()
    record.save()
    _log_action(record, user, ReviewAction.Action.LOCK, note, previous, _snapshot(record))
    return record


def edit_record(
    record: EmissionRecord,
    user,
    *,
    raw_value=None,
    raw_unit=None,
    note="",
) -> EmissionRecord:
    if record.review_status == EmissionRecord.ReviewStatus.LOCKED:
        raise ValidationError("Locked records cannot be edited.")

    previous = _snapshot(record)
    changed = False

    if raw_value is not None:
        record.raw_value = Decimal(str(raw_value))
        prev_raw = Decimal(previous["raw_value"])
        if prev_raw and prev_raw != 0:
            ratio = record.raw_value / prev_raw
            record.normalized_value_kg = record.normalized_value_kg * ratio
        changed = True
    if raw_unit is not None:
        record.raw_unit = raw_unit
        changed = True

    if not changed:
        raise ValidationError("No editable fields provided.")

    record.is_edited = True
    record.review_status = EmissionRecord.ReviewStatus.PENDING
    record.reviewed_by = None
    record.reviewed_at = None
    record.save()
    _log_action(record, user, ReviewAction.Action.EDIT, note, previous, _snapshot(record))
    return record


def bulk_approve_job(job, user) -> int:
    """Approve all PENDING rows without ERROR flags for a job."""
    qs = job.emission_records.filter(
        review_status=EmissionRecord.ReviewStatus.PENDING,
    ).exclude(
        anomaly_flags__severity=AnomalyFlag.Severity.ERROR,
    ).distinct()

    count = 0
    for record in qs:
        approve_record(record, user, note="Bulk approved")
        count += 1
    return count
