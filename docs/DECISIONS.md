# Design Decisions — Breathe ESG Ingestion Prototype

Every ambiguity resolved, what was chosen, why, and what I'd ask the PM.

---

## 1. SAP: Flat file export (ME2M) — not OData, BAPI, or IDoc

**Chosen:** Semicolon/tab-delimited flat file upload (`.csv` / `.txt`).

**Alternatives considered:**

| Mechanism | Why not for prototype |
|-----------|----------------------|
| **SAP OData** | Requires SAP Gateway service activation, CSRF tokens, and direct SAP system access with service user credentials. Not available without client IT provisioning. |
| **SAP BAPI/RFC** | Requires `pyrfc` + SAP NetWeaver RFC SDK, VPN to client SAP, and ABAP custom function modules. Standard for real integration but weeks of client IT work. |
| **SAP IDoc** | Requires middleware (SAP PI/PO or Integration Suite) to receive IDocs and forward to our API. Clients without integration infrastructure cannot use this. |
| **Flat file (SE16/ME2M)** | Facilities and procurement teams export manually from SAP GUI. **Most common real-world handoff** for clients without integration infrastructure. |

**What real SAP integration would require:**

1. SAP Basis team creates RFC service user with read access to MM tables (MSEG, EKKO, EKPO)
2. Network: VPN or SAP Cloud Connector to expose RFC
3. Middleware job (Celery beat or SAP CPI) polling ME2M nightly
4. Plant master data sync (WERKS → country, grid region) from SAP customising tables (T001W)
5. Material master sync (MATNR → MATKL, emission category) from MARA/MARC

**Subset handled:** ME2M purchase-order line exports with MANDT, BUKRS, WERKS, MATNR, MATKL, MENGE, MEINS, NETWR, WAERS, BLDAT, BKTXT, LIFNR.

**Ignored:** Goods receipt (MIGO), invoice verification (MIRO), batch/serial numbers, cost center allocation, multi-company-code consolidation rules.

---

## 2. Utility: Portal CSV — not Green Button API or PDF parsing

**Chosen:** CSV export from utility customer portal.

**Alternatives:**

| Mechanism | Why not |
|-----------|---------|
| **Green Button / ESPI API** | Requires utility-specific OAuth, utility participation (not all utilities support it), and per-utility API adapters. PG&E supports it; many Indian/EU utilities do not. |
| **PDF bill parsing (pdfplumber)** | Realistic for one-off uploads but brittle — every utility has different PDF layouts. Included in requirements stack for future work; CSV chosen as primary path for reliability. |
| **Portal CSV** | Available from **every major utility portal** (PG&E, National Grid, Tata Power). Facilities teams already download these monthly. |

**What I'd ask the PM:**

> "For Scope 2 reporting, do we use **location-based** grid factors only, or does this client have **RECs/PPAs** for market-based accounting? That changes which factor we apply."

> "Billing periods don't align to calendar months — do auditors want emissions attributed to **bill end date**, **daily proration**, or **calendar month pro-rata**?"

---

## 3. Travel: Concur TRX CSV — not Concur Extract API

**Chosen:** CSV export from Concur Expense admin console (TRX extract format).

**Alternatives:**

| Mechanism | Why not |
|-----------|---------|
| **Concur Extract API v2** | Requires SAP Concur partnership credentials, OAuth client registration, and admin approval. Not available for intern prototypes. |
| **Navan API** | Similarly gated behind enterprise contract. |
| **CSV export** | Universally available from Concur admin → Reporting → Extract Definitions. Real handoff in practice. |

**Subset handled:** ExpenseType classification (Airfare, Hotel, Taxi/Rail/Car Rental), airport codes, cabin class, room nights, distance when present.

**Ignored:** Personal car mileage logs, per-diem meals (non-lodging), carbon offset purchases, multi-passenger ticket splitting.

---

## 4. Celery async ingestion — not synchronous upload

**Why async:**

- SAP files can be 50–50,000 rows; parsing + factor lookup + dedup in-request would timeout HTTP (30s on Railway)
- Failed rows shouldn't block successful rows — partial success with error_log
- Worker can retry without re-uploading (job reads stored `raw_file`)
- Scales to multiple concurrent uploads per tenant

**Local dev:** `CELERY_TASK_ALWAYS_EAGER=True` runs inline without Redis for developer convenience.

**Production:** Separate Railway worker service with Redis broker.

---

## 5. Pint for unit conversion — not a hardcoded lookup table

**Why Pint:**

- SAP units (L, KG, M3, TO, KWH) map to SI units with dimensional analysis
- Prevents unit mismatch bugs (e.g. confusing metric tonnes with US tons)
- Extensible when clients add uncommon units (BTU, therms)

**What we still hardcode:** Emission factors (kgCO₂e per unit) — Pint handles dimensional conversion, not carbon intensity. Factors come from DEFRA/eGRID/IEA tables stored in `emission_factors.py`.

---

## 6. SAP material group (MATKL) → Scope classification

| MATKL range | Classification | Scope |
|-------------|---------------|-------|
| 1680–1686 | Fuel materials (diesel, gas, LPG, heating oil) | **1** |
| All other | Purchased goods (steel, packaging, IT hardware) | **3** |

Based on SAP standard material group conventions for combustibles vs. general procurement. In production, this mapping would live in a **client-specific config table** maintained by the sustainability team — SAP MATKL meanings vary by industry.

**Anomaly:** MATKL 4500 with unit `ST` (pieces) flagged as UNKNOWN_UNIT for fuel calc — ST is valid SAP UoM but not convertible to mass/volume for emission factors.

---

## 7. Emission factor sources

| Source type | Factor library | Rationale |
|-------------|---------------|-----------|
| SAP fuel | **DEFRA 2023** | UK government GHG Conversion Factors — widely cited, versioned annually, covers liquid fuels and gas by unit |
| Utility (US) | **EPA eGRID 2023** | Subregion grid factors — standard for US Scope 2 location-based |
| Utility (India) | **IEA 2022** | Grid emission factor for India (~0.708 kg/kWh) |
| Utility (UK) | **DEFRA 2023** | UK grid factor (~0.207 kg/kWh) |
| Travel flights | **DEFRA 2023** with RF multiplier | Distance-based with cabin class multipliers |
| Travel hotels | **DEFRA 2023** spend-based | 0.507 kgCO₂e/USD |
| Travel ground | **DEFRA 2023** | Distance or spend fallback |

**Why DEFRA as default:** Versioned, publicly downloadable, covers all activity types in this prototype, and is commonly used by UK/EU sustainability teams. US clients would typically prefer EPA GHG Hub for fuels — noted as production enhancement.

**Critical rule:** Factors stored on `EmissionRecord.emission_factor_used` at ingestion — never recomputed at query time.

---

## 8. Monetary values ignored for emission calculations

SAP `NETWR` (net value) is parsed and used only for anomaly detection (negative = credit memo). Emission calc uses `MENGE × factor` only.

Rationale: Spend-based factors require currency normalization (see TRADEOFFS.md). Quantity-based is more defensible for fuels; spend-based used only where quantity unavailable (hotels, ground fallback).

---

## 9. Questions I'd ask the PM

1. **Billing period alignment:** Calendar month vs. bill-end vs. daily proration for utility Scope 2?
2. **Plant code master data:** Who owns WERKS → country/grid region mapping — client MDM team or do we maintain it?
3. **Market-based vs. location-based electricity:** Does client have RECs/PPAs?
4. **Approval workflow:** Can ERROR-flagged rows ever be approved with override + justification, or hard block?
5. **Re-ingestion policy:** If client re-uploads corrected file, do we supersede old rows or keep both versions?
6. **Multi-currency:** Client operates in EUR, INR, USD — which FX rate for spend-based travel factors?

---

## 10. Auth model

JWT (simplejwt) chosen over session cookies because:
- Frontend on Vercel (different domain) — cookies require complex CSRF/CORS setup
- Stateless API scales horizontally on Railway
- Token refresh handles 8-hour analyst sessions

Registration endpoint creates org + admin — prototype bootstrap only. Production would use invite-only provisioning.

---

## 11. Analyst UX decisions

- **Bulk approve** skips rows with ERROR-level anomaly flags (not WARNING) — balances speed with safety
- **Lock is irreversible** — mirrors audit sign-off; analyst must approve first
- **Edit resets to PENDING** — edited rows require re-review
- **Upload redirects to job detail** — immediate feedback loop for non-engineers
- **Sample file downloads** in UI — evaluators can test without hunting repo

---

## 12. Deployment choices

| Component | Provider | Rationale |
|-----------|----------|-----------|
| API + Worker | **Railway** | Simple PostgreSQL + Redis plugins, dual-service for web/worker, health checks |
| Frontend | **Vercel** | Zero-config Vite deploy, edge CDN, env vars for API URL |
| File storage | Local filesystem (Railway ephemeral) | Prototype acceptable; production needs S3 (see TRADEOFFS.md) |
