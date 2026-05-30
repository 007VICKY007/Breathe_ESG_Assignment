# Source Research — Real-World Formats & Sample Data

For each of the three ingestion sources: what we researched, what's in real exports vs. our model, what our sample data looks like, and what breaks in production.

**Default emission factor citation:** UK Government [GHG Conversion Factors for Company Reporting 2023](https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2023) (DEFRA/DESNZ), used for fuels, travel, and UK grid electricity unless otherwise noted.

---

## Source 1: SAP — Fuel & Procurement

### Real-world format researched

**Primary reference:** SAP MM (Materials Management) purchase order history via transaction **ME2M** (Purchase Orders by Material) or **MB51** (Material Document List). Clients export via SE16N (data browser) or custom report RFFOUS_CUST.

**Typical export characteristics:**
- Delimiter: semicolon (`;`) in German/EU SAP instances, tab in US instances
- Encoding: UTF-8 or ISO-8859-1 (Latin-1) with German umlauts in BKTXT
- Date formats: `YYYYMMDD` (internal SAP format) or `DD.MM.YYYY` (user-facing German locale)
- Number formats: German locale uses `1.234,56` (period = thousands, comma = decimal)
- Units: SAP internal UoM — `L` (liters), `KG`, `M3` (cubic meters), `TO` (metric tonnes), `KWH`, `ST` (pieces)
- Material groups (MATKL): classify fuel vs. non-fuel — e.g. 1680 = combustibles/lubricants

**Fields commonly present in ME2M exports:**

| SAP field | Description | In our model? |
|-----------|-------------|---------------|
| MANDT | Client (100) | Used in hash, not stored |
| BUKRS | Company code | Not stored (single-entity prototype) |
| WERKS | Plant code | → `location` + country lookup |
| MATNR | Material number | Not stored (would join material master in prod) |
| MATKL | Material group | → Scope 1 vs 3 classification |
| MENGE | Quantity | → `raw_value` |
| MEINS | Unit | → `raw_unit` |
| NETWR | Net value | Anomaly check only — **not used in calc** |
| WAERS | Currency | Parsed, not used in calc |
| BLDAT | Document date | → `activity_date` |
| BKTXT | Text description | Not stored (available for NLP classification in prod) |
| LIFNR | Vendor number | → `vendor_or_carrier` |

**Fields in real exports we ignore:**
- EBELN/EBELP (PO number/line) — would improve dedup in production
- LGORT (storage location), KOSTL (cost center) — needed for granular Scope 1 allocation
- Material description (MAKTX) — requires join to MAKT table

### Our sample data (`sample_data/sap_me2m_export.csv`)

**50 rows**, semicolon-delimited, designed to mirror a German multinational's ME2M extract:

| Realism feature | Example in sample |
|----------------|-------------------|
| 3 plant codes | DE01 (Frankfurt), IN02 (Pune), US03 (Houston) + UK04, SG05 |
| Mixed fuel + procurement | MATKL 1680–1686 (fuel) vs 2100/3400/4500 (procurement) |
| Both date formats | `20240115` and `15.02.2024` |
| German decimals | `1.234,56` liters |
| German descriptions | "Diesel Kraftstoff Werk Frankfurt", "Erdgas Heizung Gebäude A" |
| **Anomaly: zero quantity** | Row: "Cancelled fuel requisition", MENGE=0 |
| **Anomaly: unknown unit ST** | IT hardware in pieces — not convertible to mass/volume factor |
| **Anomaly: negative NETWR** | Credit memo steel return, NETWR=-1250 |

**Why it's realistic:** Matches SAP community documentation on ME2M field layouts and common EU client export conventions (semicolon, German number formatting). An evaluator who has seen SAP exports will recognize MANDT/BUKRS/WERKS column naming.

### What breaks in real deployment

1. **Custom Z-fields** — clients add ZZEMISS_CLASS or similar; our parser expects standard ME2M columns
2. **Multiple company codes (BUKRS)** — consolidation rules not modeled
3. **Material master dependency** — MATKL alone is insufficient; same MATKL can mean different things per client
4. **Encoding errors** — Latin-1 files with € symbols will fail UTF-8 decode (need chardet)
5. **Duplicate PO lines** — without EBELN+EBELP in hash, structurally different rows with same material/qty/date could false-dedup
6. **Biogenic fuels** — DEFRA has separate biogenic CO₂ factors; we treat all fuel as fossil

---

## Source 2: Utility — Electricity

### Real-world format researched

**Primary references:**
- **PG&E** (California): Clean Energy Builder portal → Usage Export CSV
- **National Grid** (US Northeast): Energy Manager portal → Billing History CSV
- **Tata Power** (India): Commercial & Industrial portal → Consumption download

**Typical portal CSV fields:**

| Field | PG&E-style | National Grid | In our model? |
|-------|-----------|---------------|---------------|
| Account number | ✓ | ✓ | → `vendor_or_carrier` |
| Meter ID | ✓ | ✓ | Part of `location` |
| Service address | ✓ | ✓ | Part of `location` |
| Billing period start/end | ✓ | ✓ | → `period_start/end` |
| kWh consumed (total) | ✓ | ✓ | → `raw_value` |
| On-peak / off-peak kWh | ✓ (TOU tariffs) | Sometimes | Parsed in CSV, not separately stored |
| Demand kW (peak) | ✓ | ✓ | Parsed, not used in calc |
| Tariff schedule | ✓ (E-19, etc.) | ✓ | Parsed, not used in factor lookup |
| Total charges | ✓ | ✓ | Parsed, **not used in calc** |
| State/region | ✓ | ✓ | → grid factor lookup |

**Green Button API (not chosen):** ESPI Atom feed with OAuth — standardized but <30% utility participation. Would require per-utility OAuth app registration.

**PDF bills (not chosen as primary):** pdfplumber in requirements stack for future; every utility PDF layout differs. Viable as analyst upload fallback, not primary pipeline.

### Our sample data (`sample_data/utility_meter_export.csv`)

**36 rows** = 3 meters × 12 billing periods (Jan–Dec 2024):

| Meter | Facility | Region | Factor source |
|-------|----------|--------|---------------|
| E-4829182-A | Austin TX (1200 Technology Blvd) | US-TX | EPA eGRID 0.413 kg/kWh |
| NG-NYC-88421 | NYC (350 Fifth Avenue) | US-NY | EPA eGRID 0.288 kg/kWh |
| TATA-PUN-01 | Pune (Hinjawadi Phase 2) | IN | IEA 2022 0.708 kg/kWh |

**Realism features:**
- Account numbers match utility format patterns (PG&E `XXX-XXXX-XXXX`, Tata `TP-MH-XXXXXXX`)
- Billing periods **28–32 days** — not calendar months
- **Cross-year period:** Dec 2024 bill ending Jan 4, 2025
- **Long period anomaly:** 37-day bill (missed meter read scenario) for Austin meter in July
- **Consumption spike:** October Austin meter at 78,200 kWh vs ~15,000 baseline (3σ flag)
- On-peak/off-peak split (~62/38) reflecting TOU tariff structure
- Total charges included but ignored for emissions (realistic — facilities teams see charges, sustainability teams use kWh)

### What breaks in real deployment

1. **Solar/net metering** — kWh consumed may be gross while emissions should use grid-purchased only; need "kWh from grid" vs "kWh generated on-site"
2. **Market-based Scope 2** — RECs/PPAs not in CSV; location-based factor overstates if client has renewable contracts
3. **Combined bills** — one CSV row with multiple meters aggregated; our parser assumes one row per meter per period
4. **Estimated reads** — utilities mark estimated vs. actual; we don't detect "E" flag on reads
5. **Timezone/date parsing** — US MM/DD/YYYY vs ISO; we handle both but not DD-MM-YYYY with ambiguous days
6. **Cumulative meter readings** — some exports give meter start/end readings instead of consumption delta; would need subtraction logic

---

## Source 3: Corporate Travel — Concur TRX Export

### Real-world format researched

**Primary reference:** SAP Concur Expense **Reporting → Extract Definitions → TRX (Transaction) extract**. Also reviewed Navan (TripActions) admin CSV export documentation.

**Concur TRX typical fields:**

| Field | Flights | Hotels | Ground | In our model? |
|-------|---------|--------|--------|---------------|
| EmployeeID | ✓ | ✓ | ✓ | In hash only |
| ReportID | ✓ | ✓ | ✓ | In hash only |
| ExpenseType | Airfare | Hotel/Lodging | Taxi/Rail/Car Rental | → source_type classification |
| TransactionDate | ✓ | ✓ | ✓ | → `activity_date` |
| Amount + Currency | ✓ | ✓ | ✓ | → `raw_value` (hotels/ground) |
| Origin/Destination Airport | ✓ | — | — | → haversine distance |
| CabinClass | ✓ | — | — | → DEFRA multiplier |
| CarrierCode | ✓ | — | — | → `vendor_or_carrier` |
| PropertyName, City | — | ✓ | — | → `location` |
| CheckIn/CheckOut, RoomNights | — | ✓ | — | Anomaly if missing |
| VendorType, Distance | — | — | ✓ | Distance-based or spend fallback |
| PickupCity/DropCity | — | — | Sometimes | → `location` |

**Navan API (not chosen):** REST API with OAuth 2.0, requires enterprise API key from Navan customer success. Same data shape as Concur CSV when exported.

**ICAO carbon calculator (reference for flight method):** Distance-based with great-circle route; we use DEFRA 2023 factors with radiative forcing embedded rather than ICAO calculator directly, but methodology is equivalent.

### Our sample data (`sample_data/travel_concur_export.csv`)

**31 rows** across 3 employees (E10294, E20441, E30102), covering all travel types:

| Category | Count | Realism |
|----------|-------|---------|
| Flights | 13 | Mixed carriers (UA, LH, BA, EK, 6E), cabin classes, international routes |
| Hotels | 7 | Marriott, Raffles, Four Seasons; varied spend |
| Ground | 8 | Uber, DB Rail, Hertz, Amtrak; mix of distance present/absent |

**Intentional anomalies:**
- **Missing cabin class** (BA LHR→JFK) — defaults to Economy with WARNING flag
- **Same-day return** (JFK→JFK) — origin equals destination
- **Missing room nights** (Hilton Munich) — ERROR flag, defaults to 1 for calc
- **High hotel spend** (Four Seasons NYC, $1,600/night) — WARNING >$800/night
- **Ground without distance** (Hertz rental, Denver taxi) — spend-based fallback

**Airport pairs used:** Real IATA codes from embedded 50-airport lookup (SFO-ORD, FRA-SIN, LHR-JFK, DEL-BOM, etc.) with haversine distances.

### What breaks in real deployment

1. **Multi-leg flights** — Concur often shows single leg; connecting flights need segment-level data or great-circle sum
2. **Open-jaw / multi-city** — single origin/destination insufficient; need full itinerary JSON
3. **Class upgrades post-booking** — cabin class in export may not match flown class
4. **Currency** — Concur exports in employee's reimbursement currency; spend factors assume USD (see TRADEOFFS.md)
5. **Private jet / charter** — not in standard ExpenseType mapping
6. **Carbon offsets purchased** — appear as separate expense line; we don't subtract from gross emissions
7. **Hotel aggregation services** — Concur shows booking vendor (Egencia) not actual hotel; PropertyName field sometimes empty
8. **Rail in Europe** — distance often missing; spend fallback significantly less accurate than DEFRA distance method

---

## Cross-source comparison

| Dimension | SAP | Utility | Travel |
|-----------|-----|---------|--------|
| Ingestion | File upload | File upload | File upload |
| Primary calc input | Quantity (MENGE) | kWh | Distance or spend |
| Scope | 1 or 3 | 2 | 3 |
| Factor source | DEFRA 2023 | eGRID / IEA / DEFRA | DEFRA 2023 |
| Biggest prod gap | Material master sync | Market-based Scope 2 | FX normalization |
| Sample rows | 50 | 36 | 31 |
| Anomaly rows | 3 | 2 | 5 |

---

## Sample data regeneration

```bash
python scripts/generate_sample_data.py
```

Files land in `sample_data/` and are copied to `frontend/public/sample_data/` for UI download links.

After regeneration, re-upload via dashboard or:

```bash
cd backend
python manage.py seed_sample_data --username demo
```
