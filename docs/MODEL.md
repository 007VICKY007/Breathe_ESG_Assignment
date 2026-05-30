# Data Model — Breathe ESG Ingestion Prototype

This document describes the canonical schema, field-level justifications, and the mechanisms that enforce data integrity across tenants and audit cycles.

---

## Entity relationship overview

```
Organization (tenant)
 ├── User (ANALYST | ADMIN)
 ├── DataSource (config per source type)
 ├── IngestionJob (one per upload)
 │    └── EmissionRecord (canonical row)
 │         ├── AnomalyFlag (system-detected issues)
 │         └── ReviewAction (analyst decisions, append-only)
 └── HistoricalEmissionRecord (django-simple-history shadow table)
```

Every business table except `Organization` itself carries a **`tenant` FK** to `Organization`. There is no shared data between tenants.

---

## Organization

| Field | Type | Justification |
|-------|------|---------------|
| `id` | UUID PK | Stable identifier across exports; no sequential leakage |
| `name` | CharField | Display name for analyst UI |
| `slug` | SlugField | URL-safe tenant key for bootstrap/seeding |
| `is_active` | Boolean | Soft-disable without deleting audit history |

**Why UUID primary keys (not integer)?**

Integer PKs leak information (record counts, creation order) and complicate data migration when merging systems. UUIDs are stable across re-ingestion, database restores, and cross-environment seeding. For a multi-tenant SaaS prototype where evaluators will inspect API responses, UUIDs also prevent guessing adjacent record IDs.

---

## User

Extends Django `AbstractUser` with:

| Field | Justification |
|-------|---------------|
| `organization` FK | **Mandatory tenant scope** — every user belongs to exactly one org |
| `role` | `ANALYST` (review only) or `ADMIN` (future: user management) |

Constraint: `unique_email_per_org` — same email can exist in different tenants (realistic for consultants).

Auth: JWT via `djangorestframework-simplejwt`. Token payload includes user ID; tenant resolved from `User.organization` on every request.

---

## IngestionJob

Tracks one file upload through the async pipeline.

| Field | Justification |
|-------|---------------|
| `source_category` | SAP / UTILITY / TRAVEL — drives parser selection |
| `original_filename` | Analyst-visible provenance |
| `raw_file` | Stored upload for re-processing and audit ("what file produced this?") |
| `status` | PENDING → PROCESSING → DONE \| FAILED |
| `rows_total/created/skipped/failed` | Operational metrics for analyst dashboard |
| `error_log` | JSON array of `{row, message}` — parse failures without failing entire job |
| `created_by` FK | Who initiated the upload |

**Source-of-truth tracking:** Every `EmissionRecord` links back to `ingestion_job`, which links to `raw_file` and `created_at`. An auditor can answer: *which file, uploaded when, by whom, produced this row?*

---

## EmissionRecord (canonical normalized row)

The heart of the model. All three source types collapse into this single shape.

| Field | Type | Justification |
|-------|------|---------------|
| `id` | UUID PK | Stable row identity |
| `tenant` | FK | Row-level isolation |
| `ingestion_job` | FK | Source-of-truth chain |
| `source_type` | Enum | SAP_FUEL, SAP_PROCUREMENT, UTILITY_ELECTRICITY, TRAVEL_FLIGHT, TRAVEL_HOTEL, TRAVEL_GROUND |
| `scope` | 1 \| 2 \| 3 | GHG Protocol scope — required on every row |
| `activity_date` | Date | **When the emission occurred** — not ingestion date |
| `period_start/end` | Date, nullable | Utility billing periods (often ≠ calendar month) |
| `raw_value` | Decimal | Quantity as reported by source |
| `raw_unit` | CharField | Unit as reported (liters, kwh, km, usd) |
| `normalized_value_kg` | Decimal | **Always kgCO₂e** after conversion |
| `emission_factor_used` | Decimal | Factor frozen at ingestion time |
| `emission_factor_source` | CharField | e.g. "DEFRA 2023", "EPA eGRID 2023" |
| `location` | CharField | Plant code, meter address, airport pair |
| `vendor_or_carrier` | CharField | LIFNR, utility account, airline |
| `source_row_hash` | SHA-256 hex | Dedup key (see below) |
| `is_edited` | Boolean | True if analyst changed post-ingestion values |
| `review_status` | Enum | PENDING → APPROVED \| REJECTED → LOCKED |
| `reviewed_by/at` | FK + DateTime | Who signed off and when |

### Unique constraint: `(tenant, source_row_hash)`

Prevents duplicate ingestion of the same source row within a tenant. Celery task re-runs are idempotent.

---

## Multi-tenancy isolation

**Enforcement layer: ORM queryset filter — not application logic scattered in views.**

```python
class TenantQuerysetMixin:
    def get_queryset(self):
        return super().get_queryset().filter(tenant=self.request.user.organization)
```

Every list/detail/review endpoint uses this mixin. There are **no hardcoded tenant IDs** anywhere in the codebase. Cross-tenant data leakage would require bypassing the mixin deliberately.

JWT auth ensures `request.user.organization` is always set (registration creates org + user atomically).

---

## source_row_hash — deduplication

Computed as `SHA-256(json.dumps(raw_row, sort_keys=True))` at parse time.

- Same file uploaded twice → duplicates skipped, `rows_skipped_duplicate` incremented
- Celery retry on same job → no double-insert (hash already exists)
- Hash is per-tenant, so two clients can ingest identical SAP exports without collision

---

## Audit trail — django-simple-history

`EmissionRecord` has `history = HistoricalRecords()`.

**Why django-simple-history over custom audit signals?**

1. **Battle-tested** — handles field-level diffs, user attribution, timestamps automatically
2. **Middleware integration** — `HistoryRequestMiddleware` stamps `history_user` from the JWT-authenticated request
3. **Queryable** — `record.history.all()` powers `GET /records/{id}/history/`
4. **No signal spaghetti** — custom signals would duplicate what the library already does and are easy to miss on bulk operations

**Complement: `ReviewAction` model**

Simple-history tracks *value changes* (raw_value, review_status). `ReviewAction` tracks *decisions* (APPROVE, REJECT, EDIT, LOCK) with analyst notes and before/after snapshots. Together they answer both "what changed?" and "who approved it?".

**Lock semantics:** `review_status=LOCKED` is irreversible. Locked rows reject PATCH and approve/reject. This mirrors auditor requirements: signed-off data must not change.

---

## Scope 1/2/3 determination

| Source | Scope | Logic |
|--------|-------|-------|
| SAP fuel (MATKL 1680–1686) | **1** | Direct combustion at owned/controlled facilities |
| SAP procurement (other MATKL) | **3** | Purchased goods and services |
| Utility electricity | **2** | Indirect energy — location-based grid factor |
| Travel (all categories) | **3** | Category 6: Business travel |

Scope is set at **parse time** and stored on the row. It is not recomputed at query time.

---

## period_start / period_end — non-calendar billing

Utility bills rarely align to calendar months. A January bill might cover Dec 15 – Jan 18 (35 days).

We store the **actual billing period** on each row:
- `activity_date` = `period_end` (reporting convention: attribute to period end)
- `period_start/end` preserved for proration and anomaly detection (period > 35 days flagged)

Future enhancement (not built): daily proration `kWh / days` for cross-month reporting aggregation.

---

## normalized_value_kg — computation by source

Factors are **stored on the record at ingestion** — never looked up at query time. Emission factor libraries update annually; historical records must reflect what was used.

### SAP fuel (Scope 1)

```
normalized_value_kg = MENGE × emission_factor_kg_per_unit
```

Factor selected by: `plant_code → country → unit (L, KG, M3, TO)` from DEFRA 2023-style table.

Example: 4,250.75 L diesel at DE plant → `4250.75 × 2.51230 = 10,678.9 kgCO₂e`

### SAP procurement (Scope 3)

```
normalized_value_kg = MENGE × PROCUREMENT_FACTOR_KG_PER_EUR
```

Quantity-only proxy (no spend-based calc in prototype — monetary values ignored per spec).

### Utility electricity (Scope 2)

```
normalized_value_kg = kwh_consumed × grid_factor_kg_per_kwh
```

Factor by `state_region` (e.g. US-TX → EPA eGRID 0.413 kg/kWh).

### Travel flight (Scope 3)

```
distance_km = haversine(origin_airport, destination_airport)
factor = FLIGHT_KG_PER_KM × cabin_multiplier
normalized_value_kg = distance_km × factor
```

Cabin multipliers (DEFRA 2023): Economy 1.0, Premium Economy 1.33, Business 1.54, First 2.40.

### Travel hotel (Scope 3)

```
normalized_value_kg = amount_usd × HOTEL_SPEND_FACTOR_KG_PER_USD
```

DEFRA 2023 spend-based: 0.507 kgCO₂e/USD.

### Travel ground (Scope 3)

```
if distance_km present:
    normalized_value_kg = distance_km × GROUND_DISTANCE_FACTOR
else:
    normalized_value_kg = amount_usd × GROUND_SPEND_FACTOR  # fallback
```

---

## AnomalyFlag

| Field | Justification |
|-------|---------------|
| `flag_type` | Machine-readable code (ZERO_QUANTITY, CONSUMPTION_SPIKE, etc.) |
| `severity` | ERROR (blocks approval) or WARNING (informational) |
| `message` | Human-readable for analyst UI |
| `affected_field` | Which source column triggered the flag |

Every flag has all four attributes per spec requirement.

---

## ReviewAction

Append-only log. No UPDATE or DELETE endpoints exposed.

Stores `previous_values` and `new_values` JSON snapshots for EDIT actions, enabling audit log display without joining history tables.

---

## Indexes

Composite indexes on `(tenant, review_status)`, `(tenant, source_type)`, `(tenant, activity_date)`, `(tenant, source_row_hash)` ensure filtered dashboards remain fast as row counts grow per org.
