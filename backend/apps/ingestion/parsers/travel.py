"""
Concur TRX-style travel CSV — flights (haversine), hotels, ground.
"""
import csv
import io
import logging
import math
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from apps.emissions.models import EmissionRecord
from apps.ingestion.factors.emission_factors import (
    CABIN_MULTIPLIERS,
    EMISSION_FACTOR_SOURCE_DEFRA,
    FLIGHT_KG_PER_KM,
    GROUND_DISTANCE_FACTOR_KG_PER_KM,
    GROUND_SPEND_FACTOR_KG_PER_USD,
    HOTEL_SPEND_FACTOR_KG_PER_USD,
)
from apps.ingestion.services.hashing import compute_row_hash

from .base import ParseResult, ParsedEmissionRow

logger = logging.getLogger(__name__)

# Top airports — lat/lon for haversine (subset of 50; expandable)
AIRPORTS: dict[str, tuple[float, float]] = {
    "LHR": (51.4700, -0.4543), "JFK": (40.6413, -73.7781), "LAX": (33.9416, -118.4085),
    "SFO": (37.6213, -122.3790), "ORD": (41.9742, -87.9073), "DFW": (32.8998, -97.0403),
    "ATL": (33.6407, -84.4277), "DXB": (25.2532, 55.3657), "SIN": (1.3644, 103.9915),
    "HKG": (22.3080, 113.9185), "FRA": (50.0379, 8.5622), "CDG": (49.0097, 2.5479),
    "AMS": (52.3105, 4.7683), "DEL": (28.5562, 77.1000), "BOM": (19.0896, 72.8656),
    "BLR": (13.1986, 77.7066), "NRT": (35.7720, 140.3929), "SYD": (-33.9399, 151.1753),
    "MEL": (-37.6690, 144.8410), "YYZ": (43.6777, -79.6248), "SEA": (47.4502, -122.3088),
    "BOS": (42.3656, -71.0096), "IAD": (38.9531, -77.4565), "MIA": (25.7959, -80.2870),
    "DEN": (39.8561, -104.6737), "PHX": (33.4373, -112.0078), "IAH": (29.9902, -95.3368),
    "MUC": (48.3538, 11.7861), "ZRH": (47.4647, 8.5492), "MAD": (40.4983, -3.5676),
    "BCN": (41.2974, 2.0833), "FCO": (41.8003, 12.2389), "IST": (41.2753, 28.7519),
    "DOH": (25.2609, 51.6138), "ICN": (37.4602, 126.4407), "PEK": (40.0799, 116.6031),
    "PVG": (31.1443, 121.8083), "CAN": (23.3924, 113.2988), "BKK": (13.6900, 100.7501),
    "KUL": (2.7456, 101.7099), "CGK": (-6.1256, 106.6559), "JNB": (-26.1367, 28.2411),
    "CAI": (30.1219, 31.4056), "TLV": (32.0114, 34.8867), "DUB": (53.4264, -6.2499),
    "MAN": (53.3537, -2.2750), "EDI": (55.9500, -3.3725), "OSL": (60.1976, 11.1004),
    "ARN": (59.6519, 17.9186), "CPH": (55.6180, 12.6508), "HEL": (60.3172, 24.9633),
}

FLIGHT_TYPES = frozenset({"AIRFARE", "AIR", "FLIGHT", "AIR TICKET"})
HOTEL_TYPES = frozenset({"HOTEL", "LODGING", "ACCOMMODATION", "HOTEL ROOM"})
GROUND_TYPES = frozenset({"TAXI", "RAIL", "TRAIN", "CAR RENTAL", "GROUND", "RIDESHARE", "UBER", "LYFT"})


def _parse_date(value: str) -> date | None:
    value = (value or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_decimal(value: str) -> Decimal | None:
    try:
        text = str(value).strip().replace("$", "").replace(",", "")
        return Decimal(text) if text else None
    except InvalidOperation:
        return None


def _haversine_km(origin: str, dest: str) -> Decimal | None:
    o = AIRPORTS.get((origin or "").strip().upper())
    d = AIRPORTS.get((dest or "").strip().upper())
    if not o or not d:
        return None
    lat1, lon1, lat2, lon2 = map(math.radians, [o[0], o[1], d[0], d[1]])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    km = 6371.0 * 2 * math.asin(math.sqrt(a))
    return Decimal(str(round(km, 2)))


def _normalize_cabin(value: str) -> str:
    v = (value or "").strip().upper()
    if not v:
        return "ECONOMY"
    if "FIRST" in v:
        return "FIRST"
    if "BUSINESS" in v:
        return "BUSINESS"
    if "PREMIUM" in v:
        return "PREMIUM_ECONOMY"
    return "ECONOMY"


def _classify_expense(expense_type: str) -> str | None:
    et = (expense_type or "").strip().upper()
    if et in FLIGHT_TYPES or "AIR" in et:
        return "FLIGHT"
    if et in HOTEL_TYPES or "HOTEL" in et:
        return "HOTEL"
    if et in GROUND_TYPES:
        return "GROUND"
    return None


def parse_travel_file(file_content: bytes, filename: str = "") -> ParseResult:
    result = ParseResult()
    text = file_content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        result.errors.append({"row": 0, "message": "Empty travel CSV"})
        return result

    for row_number, raw in enumerate(reader, start=2):
        row = {k.strip().lower(): (v or "").strip() for k, v in raw.items()}
        anomalies: list[dict[str, Any]] = []

        try:
            expense_type = row.get("expensetype", row.get("expense_type", ""))
            category = _classify_expense(expense_type)
            if not category:
                result.warnings.append({
                    "row": row_number,
                    "message": f"Unmapped ExpenseType '{expense_type}' — skipped",
                })
                continue

            txn_date = _parse_date(row.get("transactiondate", row.get("transaction_date", "")))
            if txn_date is None:
                result.errors.append({"row": row_number, "message": "Invalid TransactionDate"})
                continue

            amount = _parse_decimal(row.get("amount", "0")) or Decimal("0")
            vendor = row.get("vendorname", row.get("vendor_name", ""))

            hash_payload = dict(row)
            row_hash = compute_row_hash(hash_payload)

            if category == "FLIGHT":
                origin = row.get("origin_airport", row.get("origin", ""))
                dest = row.get("destination_airport", row.get("destination", ""))
                cabin = _normalize_cabin(row.get("cabinclass", row.get("cabin_class", "")))
                if not row.get("cabinclass", row.get("cabin_class", "")):
                    anomalies.append({
                        "type": "MISSING_CABIN_CLASS",
                        "severity": "WARNING",
                        "message": "Cabin class missing — defaulting to economy",
                        "affected_field": "cabinclass",
                    })

                distance = _haversine_km(origin, dest)
                if distance is None:
                    result.errors.append({
                        "row": row_number,
                        "message": f"Unknown airport pair {origin}-{dest}",
                    })
                    continue

                multiplier = CABIN_MULTIPLIERS.get(cabin, Decimal("1.0"))
                factor = FLIGHT_KG_PER_KM * multiplier
                normalized = distance * factor

                if origin and dest and origin.upper() == dest.upper():
                    anomalies.append({
                        "type": "SAME_DAY_RETURN",
                        "severity": "WARNING",
                        "message": "Origin equals destination — possible same-day return",
                        "affected_field": "origin_airport",
                    })

                parsed = ParsedEmissionRow(
                    source_type=EmissionRecord.SourceType.TRAVEL_FLIGHT,
                    scope=EmissionRecord.Scope.SCOPE_3,
                    activity_date=txn_date,
                    raw_value=distance,
                    raw_unit="km",
                    normalized_value_kg=normalized,
                    emission_factor_used=factor,
                    emission_factor_source=EMISSION_FACTOR_SOURCE_DEFRA,
                    source_row_hash=row_hash,
                    location=f"{origin}-{dest}",
                    vendor_or_carrier=row.get("carriercode", vendor),
                    anomalies=anomalies,
                    row_number=row_number,
                )

            elif category == "HOTEL":
                room_nights = _parse_decimal(row.get("roomnights", row.get("room_nights", "")))
                if room_nights is None or room_nights <= 0:
                    anomalies.append({
                        "type": "MISSING_ROOM_NIGHTS",
                        "severity": "ERROR",
                        "message": "Hotel row missing room nights",
                        "affected_field": "roomnights",
                    })
                    room_nights = Decimal("1")

                per_night = amount / room_nights if room_nights else amount
                if per_night > Decimal("800"):
                    anomalies.append({
                        "type": "HIGH_HOTEL_SPEND",
                        "severity": "WARNING",
                        "message": f"Hotel spend ${per_night:.2f}/night exceeds $800 threshold",
                        "affected_field": "amount",
                    })

                factor = HOTEL_SPEND_FACTOR_KG_PER_USD
                normalized = amount * factor

                parsed = ParsedEmissionRow(
                    source_type=EmissionRecord.SourceType.TRAVEL_HOTEL,
                    scope=EmissionRecord.Scope.SCOPE_3,
                    activity_date=txn_date,
                    raw_value=amount,
                    raw_unit="usd",
                    normalized_value_kg=normalized,
                    emission_factor_used=factor,
                    emission_factor_source=EMISSION_FACTOR_SOURCE_DEFRA,
                    source_row_hash=row_hash,
                    location=row.get("propertyname", row.get("city", "")),
                    vendor_or_carrier=vendor,
                    anomalies=anomalies,
                    row_number=row_number,
                )

            else:  # GROUND
                distance = _parse_decimal(row.get("distance_km", row.get("distance", "")))
                if distance and distance > 0:
                    factor = GROUND_DISTANCE_FACTOR_KG_PER_KM
                    normalized = distance * factor
                    raw_val = distance
                    raw_unit = "km"
                else:
                    factor = GROUND_SPEND_FACTOR_KG_PER_USD
                    normalized = amount * factor
                    raw_val = amount
                    raw_unit = "usd"

                parsed = ParsedEmissionRow(
                    source_type=EmissionRecord.SourceType.TRAVEL_GROUND,
                    scope=EmissionRecord.Scope.SCOPE_3,
                    activity_date=txn_date,
                    raw_value=raw_val,
                    raw_unit=raw_unit,
                    normalized_value_kg=normalized,
                    emission_factor_used=factor,
                    emission_factor_source=EMISSION_FACTOR_SOURCE_DEFRA,
                    source_row_hash=row_hash,
                    location=f"{row.get('pickupcity', '')}-{row.get('dropcity', '')}",
                    vendor_or_carrier=row.get("vendortype", vendor),
                    anomalies=anomalies,
                    row_number=row_number,
                )

            result.records.append(parsed)

        except Exception as exc:
            logger.exception("Travel row %s failed", row_number)
            result.errors.append({"row": row_number, "message": str(exc)})

    return result
