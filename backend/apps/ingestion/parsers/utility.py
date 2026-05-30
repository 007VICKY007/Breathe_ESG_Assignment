"""
Utility portal CSV parser — billing periods, multi-meter, grid factors.
"""
import csv
import io
import logging
import statistics
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from apps.emissions.models import EmissionRecord
from apps.ingestion.factors.emission_factors import GRID_FACTORS_KG_PER_KWH
from apps.ingestion.services.hashing import compute_row_hash

from .base import ParseResult, ParsedEmissionRow

logger = logging.getLogger(__name__)

UTILITY_COLUMNS = [
    "account_number", "meter_id", "service_address", "billing_period_start",
    "billing_period_end", "kwh_consumed", "demand_kw", "tariff_code", "state_region",
]


def _parse_date(value: str) -> date | None:
    value = (value or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_decimal(value: str) -> Decimal | None:
    try:
        return Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


def _billing_days(start: date, end: date) -> int:
    return (end - start).days + 1


def _grid_factor(state_region: str) -> tuple[Decimal, str]:
    key = (state_region or "").strip().upper()
    if key in GRID_FACTORS_KG_PER_KWH:
        return GRID_FACTORS_KG_PER_KWH[key]
    if key.startswith("US-"):
        return GRID_FACTORS_KG_PER_KWH.get("US-IL", GRID_FACTORS_KG_PER_KWH["US-CA"])
    return GRID_FACTORS_KG_PER_KWH.get("GB", (Decimal("0.25"), "DEFRA 2023"))


def parse_utility_file(
    file_content: bytes,
    filename: str = "",
    historical_kwh: list[float] | None = None,
) -> ParseResult:
    result = ParseResult()
    text = file_content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        result.errors.append({"row": 0, "message": "Empty utility CSV"})
        return result

    field_map = {f.strip().lower(): f for f in reader.fieldnames}
    rows_data: list[dict[str, Any]] = []

    for idx, raw in enumerate(reader, start=2):
        row = {k.strip().lower(): (v or "").strip() for k, v in raw.items()}
        rows_data.append((idx, row))

    kwh_values = []
    for _, row in rows_data:
        kwh = _parse_decimal(row.get("kwh_consumed", ""))
        if kwh is not None:
            kwh_values.append(float(kwh))

    hist = historical_kwh or kwh_values
    mean_kwh = statistics.mean(hist) if hist else 0
    stdev_kwh = statistics.stdev(hist) if len(hist) > 1 else 0

    for row_number, row in rows_data:
        anomalies: list[dict[str, Any]] = []
        try:
            period_start = _parse_date(row.get("billing_period_start", ""))
            period_end = _parse_date(row.get("billing_period_end", ""))
            kwh = _parse_decimal(row.get("kwh_consumed", ""))

            if period_start is None or period_end is None:
                result.errors.append({"row": row_number, "message": "Invalid billing period dates"})
                continue
            if kwh is None:
                result.errors.append({"row": row_number, "message": "Invalid kwh_consumed"})
                continue

            days = _billing_days(period_start, period_end)
            if days > 35:
                anomalies.append({
                    "type": "BILLING_PERIOD_LONG",
                    "severity": "WARNING",
                    "message": f"Billing period {days} days exceeds 35 — possible missed meter read",
                    "affected_field": "billing_period_end",
                })
            if days < 20:
                anomalies.append({
                    "type": "BILLING_PERIOD_SHORT",
                    "severity": "WARNING",
                    "message": f"Billing period {days} days under 20 — possible estimate",
                    "affected_field": "billing_period_end",
                })

            if stdev_kwh > 0 and float(kwh) > mean_kwh + 3 * stdev_kwh:
                anomalies.append({
                    "type": "CONSUMPTION_SPIKE",
                    "severity": "WARNING",
                    "message": "kWh exceeds 3σ of org historical average",
                    "affected_field": "kwh_consumed",
                })

            state_region = row.get("state_region", "")
            factor, factor_source = _grid_factor(state_region)
            normalized = kwh * factor

            hash_payload = {col: row.get(col, "") for col in UTILITY_COLUMNS}
            row_hash = compute_row_hash(hash_payload)

            meter = row.get("meter_id", "")
            address = row.get("service_address", "")

            parsed = ParsedEmissionRow(
                source_type=EmissionRecord.SourceType.UTILITY_ELECTRICITY,
                scope=EmissionRecord.Scope.SCOPE_2,
                activity_date=period_end,
                period_start=period_start,
                period_end=period_end,
                raw_value=kwh,
                raw_unit="kwh",
                normalized_value_kg=normalized,
                emission_factor_used=factor,
                emission_factor_source=factor_source,
                source_row_hash=row_hash,
                location=f"{meter} | {address}",
                vendor_or_carrier=row.get("account_number", ""),
                anomalies=anomalies,
                row_number=row_number,
            )
            result.records.append(parsed)

        except Exception as exc:
            logger.exception("Utility row %s failed", row_number)
            result.errors.append({"row": row_number, "message": str(exc)})

    return result
