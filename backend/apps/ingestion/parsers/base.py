"""Structured parser contract — every parser returns records, errors, warnings."""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass
class ParsedEmissionRow:
    """Intermediate row before persistence."""

    source_type: str
    scope: int
    activity_date: date
    raw_value: Decimal
    raw_unit: str
    normalized_value_kg: Decimal
    emission_factor_used: Decimal
    emission_factor_source: str
    source_row_hash: str
    location: str = ""
    vendor_or_carrier: str = ""
    period_start: date | None = None
    period_end: date | None = None
    anomalies: list[dict[str, Any]] = field(default_factory=list)
    row_number: int = 0


@dataclass
class ParseResult:
    records: list[ParsedEmissionRow] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)

    def merge(self, other: "ParseResult") -> None:
        self.records.extend(other.records)
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
