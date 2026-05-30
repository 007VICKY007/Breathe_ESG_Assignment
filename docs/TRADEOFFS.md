# Deliberate Tradeoffs — Three Things Not Built

Per assignment requirements: three capabilities we intentionally omitted, why, and what it would take to add them.

---

## 1. Real SAP RFC/OData connection

### What we built instead
Flat file upload of ME2M/SE16 tab-separated or semicolon-separated exports, with a parser that handles SAP date formats, German decimal separators, and internal unit codes.

### Why we didn't build live SAP integration

**Technical barrier:** SAP RFC requires the proprietary SAP NetWeaver RFC SDK (not pip-installable on all platforms), a VPN or SAP Cloud Connector, and an RFC service user provisioned by the client's SAP Basis team. OData requires SAP Gateway services to be activated per entity set — most clients don't expose MM emission data via OData without a custom ABAP project.

**Time barrier:** A 4-day prototype cannot include client IT provisioning cycles (typically 2–6 weeks for SAP access).

**Judgment:** The assignment asks us to research what SAP exports look like and handle realistic shapes. Flat file is the most common handoff for clients without integration infrastructure — building RFC would produce code we cannot test or demonstrate.

### What it would take to build properly

1. **Discovery:** Identify which SAP tables/transactions hold emission-relevant data (ME2M, MB51, MC$4 depending on client)
2. **Access:** SAP Basis creates RFC user with S_RFC ACL for target function modules
3. **Infrastructure:** SAP Cloud Connector or site-to-site VPN; Celery beat job for nightly pull
4. **Mapping layer:** Material master (MARA/MARC) sync for MATKL → emission category; plant master (T001W) for geography
5. **Change data capture:** Track last extraction timestamp to pull deltas only
6. **Error handling:** SAP downtime, RFC timeouts, authorization failures — queue and alert, don't fail silently

**Estimated effort:** 3–4 weeks with client SAP access, 1 week without (mock RFC server for dev).

**Risk if rushed:** Hardcoded connection strings, untested RFC calls, and a demo that breaks the moment evaluators ask "show me the live SAP pull."

---

## 2. Automated emission factor updates

### What we built instead
Hardcoded factor tables in `apps/ingestion/factors/emission_factors.py` — DEFRA 2023, EPA eGRID 2023, IEA 2022 — frozen onto each `EmissionRecord` at ingestion time.

### Why we didn't build auto-updates

**Correctness over convenience:** Emission factors change annually (DEFRA publishes new tables each June). Auto-updating factors at query time would retroactively change historical emissions — unacceptable for audit. The spec explicitly requires factors stored at ingestion time.

**Scope:** Building a factor management system (versioned factor library, effective dates, approval workflow for factor changes, re-calculation jobs for amended factors) is a product feature in itself — not a 4-day prototype task.

### What it would take

1. **FactorVersion model:** `{source, activity_type, geography, factor, unit, effective_from, effective_to, approved_by}`
2. **Annual import job:** Parse DEFRA spreadsheet / eGRID zip on release
3. **Ingestion lookup:** Select factor where `effective_from <= activity_date < effective_to`
4. **Amendment workflow:** When factors update, flag affected records for analyst re-review (don't silently overwrite)
5. **Client overrides:** Some enterprises use custom factors from EPDs — override table per tenant

**Risk of hardcoded factors (honest assessment):**

- DEFRA 2024 factors differ ~2–5% from 2023 for some fuels — immaterial for prototype, material for audited reports
- New plant codes won't resolve to country without master data update
- Grid factors change as renewables penetration increases — stale IEA 2022 India factor understates improvement

**Mitigation in prototype:** `emission_factor_used` and `emission_factor_source` on every row document exactly what was applied. An auditor can recalculate if needed.

---

## 3. Multi-currency normalization for spend-based factors

### What we built instead
Travel hotel and ground spend-based calculations assume **USD** amounts with DEFRA kgCO₂e/USD factors. SAP procurement uses quantity × generic kg/EUR factor. Currency columns are parsed but **not used in emission math**.

### Why we didn't build FX normalization

**Missing inputs:** Spend-based emission factors are published per currency region (DEFRA: GBP and USD; EPA EEIO: USD). Converting INR → USD requires an FX rate on the **transaction date** — not provided in Concur exports (only Amount + Currency).

**Ambiguity:** Which rate? ECB daily? OANDA? Client's SAP book rate? Different choices change results by 1–3% — a PM decision, not an engineering default.

**Scope 3 complexity:** GHG Protocol allows spend-based method as a fallback when activity data unavailable, but requires EEIO tables matched to NAICS/SIC codes — we don't have industry codes in the travel export.

### What it would take

1. **FXRate model:** `{currency_pair, date, rate, source}` — daily ECB/OANDA import
2. **Normalization at ingestion:** `amount_usd = amount / fx_rate(currency, transaction_date)`
3. **Factor selection:** Match currency to appropriate EEIO/DEFRA spend factor table
4. **SAP procurement:** Use NAICS from vendor master or material group → EEIO sector mapping instead of generic kg/EUR
5. **PM policy:** Document which FX source is authoritative for audit

### The gap this creates

- A ₹245,000 hotel stay in Mumbai is treated as $245,000 USD if currency field mishandled — we avoid this by reading Currency column but prototype hotel calc uses raw Amount assuming USD when Currency=USD
- SAP rows in INR/EUR use quantity-based factors only — NETWR ignored for calc (correct per our policy)
- Real deployment **will break** for EUR-denominated Concur exports until FX normalization exists

**What I'd tell the PM:** "Spend-based is a fallback. For audit-grade Scope 3 travel, prioritize getting distance data (flights) and room nights (hotels) over amount-based calc. Budget 1 sprint for FX + EEIO if spend-based is required."

---

## Summary

| Omission | Prototype impact | Production blocker? |
|----------|-----------------|---------------------|
| Live SAP RFC | Manual file upload workflow | Yes — for automated clients |
| Auto factor updates | Frozen 2023 factors | Medium — annual manual update workable short-term |
| Multi-currency FX | USD-assumed spend factors | Yes — for non-US clients |

These omissions are **deliberate scoping**, not oversights. Each is documented with a clear path to production implementation.
