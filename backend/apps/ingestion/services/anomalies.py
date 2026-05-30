"""Post-parse anomaly rules applied during persistence."""
from decimal import Decimal

from apps.emissions.models import AnomalyFlag, EmissionRecord


def build_anomaly_objects(
    tenant_id,
    emission_record: EmissionRecord,
    anomaly_dicts: list[dict],
) -> list[AnomalyFlag]:
    flags = []
    for item in anomaly_dicts:
        flags.append(
            AnomalyFlag(
                tenant_id=tenant_id,
                emission_record=emission_record,
                flag_type=item["type"],
                severity=item["severity"],
                message=item["message"],
                affected_field=item.get("affected_field", ""),
            )
        )
    return flags


def record_has_blocking_errors(flags: list[AnomalyFlag]) -> bool:
    return any(f.severity == AnomalyFlag.Severity.ERROR for f in flags)
