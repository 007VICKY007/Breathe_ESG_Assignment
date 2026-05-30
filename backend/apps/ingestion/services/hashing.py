import hashlib
import json
from typing import Any


def compute_row_hash(payload: dict[str, Any]) -> str:
    """Deterministic SHA-256 over canonical JSON of the raw source row."""
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
