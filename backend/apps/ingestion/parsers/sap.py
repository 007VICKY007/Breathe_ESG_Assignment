"""
SAP ME2M / MM flat-file parser.
Tab or semicolon delimited; handles SAP date and unit conventions.
"""
import io
import logging
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd

from apps.emissions.models import EmissionRecord
from apps.ingestion.factors.emission_factors import (
    EMISSION_FACTOR_SOURCE_DEFRA,
    FUEL_FACTORS_KG_PER_UNIT,
    PLANT_COUNTRY,
    PROCUREMENT_FACTOR_KG_PER_EUR,
    SAP_FUEL_MATKL,
)
from apps.ingestion.services.hashing import compute_row_hash

from .base import ParseResult, ParsedEmissionRow

logger = logging.getLogger(__name__)

SAP_COLUMNS = [
    "MANDT", "BUKRS", "WERKS", "MATNR", "MATKL", "MENGE", "MEINS",
    "NETWR", "WAERS", "BLDAT", "BKTXT", "LIFNR",
]


def _detect_delimiter(sample: str) -> str:
    if sample.count(";") > sample.count("\t"):
        return ";"
    return "\t"


def _parse_sap_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    if re.fullmatch(r"\d{8}", value):
        return datetime.strptime(value, "%Y%m%d").date()
    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", value):
        return datetime.strptime(value, "%d.%m.%Y").date()
    return None


def _parse_decimal(value: str) -> Decimal | None:
    if value is None:
        return None
    text = str(value).strip().replace(" ", "")
    if not text:
        return None
    # German format: 1.234,56
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _normalize_columns(row: dict[str, Any]) -> dict[str, str]:
    return {str(k).strip().upper(): str(v).strip() if v is not None else "" for k, v in row.items()}


def _classify_row(matkl: str) -> tuple[str, int]:
    if matkl in SAP_FUEL_MATKL:
        return EmissionRecord.SourceType.SAP_FUEL, EmissionRecord.Scope.SCOPE_1
    return EmissionRecord.SourceType.SAP_PROCUREMENT, EmissionRecord.Scope.SCOPE_3


def _fuel_factor(country: str, unit: str) -> tuple[Decimal, str]:
    country_factors = FUEL_FACTORS_KG_PER_UNIT.get(country, FUEL_FACTORS_KG_PER_UNIT["DE"])
    unit_key = unit.upper()
    factor = country_factors.get(unit_key)
    if factor is None:
        raise KeyError(unit_key)
    return factor, EMISSION_FACTOR_SOURCE_DEFRA


def _procurement_factor() -> tuple[Decimal, str]:
    return PROCUREMENT_FACTOR_KG_PER_EUR, EMISSION_FACTOR_SOURCE_DEFRA


def parse_sap_file(file_content: bytes, filename: str = "") -> ParseResult:
    result = ParseResult()
    text = file_content.decode("utf-8-sig", errors="replace")
    delimiter = _detect_delimiter(text[:4096])
    logger.info("SAP parser using delimiter %r for %s", delimiter, filename)

    df = pd.read_csv(
        io.StringIO(text),
        sep=delimiter,
        dtype=str,
        keep_default_na=False,
    )
    df.columns = [c.strip().upper() for c in df.columns]

    missing = [c for c in SAP_COLUMNS if c not in df.columns]
    if missing:
        result.errors.append({
            "row": 0,
            "message": f"Missing required SAP columns: {', '.join(missing)}",
        })
        return result

    for idx, raw in df.iterrows():
        row_number = int(idx) + 2  # header + 1-based
        row = _normalize_columns(raw.to_dict())
        anomalies: list[dict[str, Any]] = []

        try:
            plant = row.get("WERKS", "")
            matkl = row.get("MATKL", "")
            unit = row.get("MEINS", "").upper()
            qty = _parse_decimal(row.get("MENGE", ""))
            netwr = _parse_decimal(row.get("NETWR", "0")) or Decimal("0")
            activity = _parse_sap_date(row.get("BLDAT", ""))

            if qty is None:
                result.errors.append({"row": row_number, "message": "Invalid MENGE quantity"})
                continue
            if activity is None:
                result.errors.append({"row": row_number, "message": "Invalid BLDAT date"})
                continue

            if qty == 0:
                anomalies.append({
                    "type": "ZERO_QUANTITY",
                    "severity": "ERROR",
                    "message": "MENGE is zero — no physical activity to convert",
                    "affected_field": "MENGE",
                })
            if netwr < 0:
                anomalies.append({
                    "type": "NEGATIVE_VALUE",
                    "severity": "ERROR",
                    "message": "NETWR is negative — credit memo or data error",
                    "affected_field": "NETWR",
                })

            country = PLANT_COUNTRY.get(plant)
            if not country:
                anomalies.append({
                    "type": "UNKNOWN_PLANT",
                    "severity": "WARNING",
                    "message": f"Plant {plant} not in master mapping; using DE factors",
                    "affected_field": "WERKS",
                })
                country = "DE"

            source_type, scope = _classify_row(matkl)

            try:
                if source_type == EmissionRecord.SourceType.SAP_FUEL:
                    factor, factor_source = _fuel_factor(country, unit)
                    normalized = qty * factor
                else:
                    factor, factor_source = _procurement_factor()
                    normalized = qty * factor
            except KeyError:
                anomalies.append({
                    "type": "UNKNOWN_UNIT",
                    "severity": "ERROR",
                    "message": f"Unrecognized SAP unit '{unit}'",
                    "affected_field": "MEINS",
                })
                factor = Decimal("0")
                factor_source = EMISSION_FACTOR_SOURCE_DEFRA
                normalized = Decimal("0")

            hash_payload = {k: row.get(k, "") for k in SAP_COLUMNS}
            row_hash = compute_row_hash(hash_payload)

            parsed = ParsedEmissionRow(
                source_type=source_type,
                scope=scope,
                activity_date=activity,
                raw_value=qty,
                raw_unit=unit.lower() if unit else "",
                normalized_value_kg=normalized,
                emission_factor_used=factor,
                emission_factor_source=factor_source,
                source_row_hash=row_hash,
                location=plant,
                vendor_or_carrier=row.get("LIFNR", ""),
                anomalies=anomalies,
                row_number=row_number,
            )
            result.records.append(parsed)

        except Exception as exc:
            logger.exception("SAP row %s failed", row_number)
            result.errors.append({"row": row_number, "message": str(exc)})

    return result
