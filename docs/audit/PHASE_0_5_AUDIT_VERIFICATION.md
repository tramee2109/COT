# PHASE 0.5 — AUDIT VERIFICATION & DATA VALIDATION REPORT
## Rigorous Factual Verification, Constraint Analysis & Corrective Findings
*Platform: Global Commodity Intelligence Platform (Copper, Silver, Platinum)*  
*Executed: 2026-11-11 | Evaluation Standard: Institutional Quantitative Research Hygiene*

---

## 1. EXECUTIVE VERIFICATION SUMMARY

This verification audit (Phase 0.5) conducted an exhaustive, empirical check on the preliminary Phase 0 feasibility audit. We verified raw file headers, parquet schemas, API endpoints, exchange terms of service, and temporal alignment metadata.

### Crucial Corrective Findings:
1. **LME Commitments of Traders (CoP) Claim Corrected:**
   - *Phase 0 Claim:* Freely downloadable and easily automated via public website.
   - *Phase 0.5 Verification:* **PARTIALLY TRUE BUT HEAVILY RESTRICTED.** Under UK MiFID II / UK MAR, LME publishes weekly aggregated positioning reports in PDF/Excel on its website on Tuesdays with a 1-week lag. However, LME Terms of Use strictly prohibit automated scraping (bots/crawlers) and commercial data redistribution without an LME Data Distribution Agreement. Historical bulk download prior to 2018 is not publicly archived on the website.
2. **Yangshan Copper Premium Proxy Claim Corrected:**
   - *Phase 0 Claim:* The SHFE/LME Copper price ratio can serve as a proxy for the Yangshan Premium with >90% correlation.
   - *Phase 0.5 Verification:* **REJECTED AS AN UNVALIDATED EMPIRICAL CLAIM.** No actual historical Yangshan spot quotation dataset exists in the workspace to calculate or prove a 90% correlation. Yangshan Premium measures the physical bonded warehouse premium in USD/t (driven by Chinese physical import arbitrage and letter of credit demand), whereas the SHFE/LME ratio is heavily driven by USD/CNY exchange rate fluctuations, Chinese 13% VAT, import tariffs, and delivery window mismatches. The proxy must be explicitly renamed `SHFE_LME_Import_Parity_Proxy` and must NEVER be presented as real physical premium data.
3. **Continuous Futures Price Data Status Corrected:**
   - *Phase 0 Claim:* Continuous daily futures prices are available from 2000 to 2026 across all files.
   - *Phase 0.5 Verification:* **NUANCED DISTINCTION DISCOVERED.** In `data/prices/hg_f.parquet`, the data covers **2021-10-18 to 2026-10-30** (1,268 trading days). The full 2000–2026 series (6,564 observations) resides in `commodity_equilibrium/07_daily_features/daily_fundamental_features.parquet`. Furthermore, this data originates from Yahoo Finance continuous front-month (`HG=F`), **not official COMEX daily exchange clearing house settlement bulletins**. It lacks Open Interest and individual contract roll breakdown.
4. **Fundamental Supply-Demand Data Verification:**
   - *Phase 0 Claim:* ICSG, WPIC, and Silver Institute supply-demand series are ready for daily modeling.
   - *Phase 0.5 Verification:* **CAUTION ON FORWARD-FILL / REVISION DATES.** The canonical data store (`fundamental_latest.parquet`) contains 14 historical annual/forecast points for Copper (2018–2025). The daily features dataset forward-filled these annual numbers across daily trading bars. **A monthly or annual fundamental release must not be treated as independent daily observations.** Lookahead bias must be mitigated by strictly using the `available_at` publication timestamp (e.g., ICSG 2024 annual figures were published on 2026-04-23).

---

## 2. AUDIT VERIFICATION OF THE FIVE SPECIFIC CLAIMS

### A. LME Commitments of Traders (CoP)
- **Account Requirement:** An ordinary registered user on LME.com can view and manually download the weekly Excel sheets.
- **Historical Depth:** Public web archive provides reports dating back to 2018 (MiFID II inception). Prior historical records require commercial LME Data Services.
- **File Format:** Weekly `.xlsx` and `.pdf`.
- **Position Classifications:** (1) Investment Funds, (2) Commercial Undertakings, (3) Investment Firms/Credit Institutions, (4) Other Financial, (5) Non-Reportable. *These map closely, but not identically, to CFTC Disaggregated categories.*
- **Commodity Coverage:** Primary metals: Copper (`CA`), Aluminium (`AH`), Zinc (`ZS`), Nickel (`NI`), Lead (`PB`), Tin (`SN`).
- **Scraping & Legal Restrictions:** Section 11 of LME Website Terms of Use explicitly prohibits automated extraction without written consent. Redistribution of raw figures is restricted.
- **Publication Schedule:** Published every **Tuesday at 13:00 London Time**, reflecting positions as of the previous **Friday close**.

### B. LME Warehouse Inventory Breakdown
LME does not publish a single generic "inventory" file; it produces distinct data products:
1. **LME Stock Movement Report (Daily Summary):**
   - *Public Status:* Free on LME website daily.
   - *Fields:* Opening Stocks, Delivered In, Delivered Out, Closing Stocks, Cancelled Warrants, On-Warrant (Live) Stocks.
   - *Publication Time:* Daily at 09:00 London Time.
   - *Usability for MVP:* **HIGH.** Total Closing Stocks and Cancelled Warrant Ratio (%) can be manually curated or ingested via authorized feeds.
2. **Detailed Warehouse Stock Report (By Location):**
   - *Fields:* Stock level per metal, per designated warehouse location (Rotterdam, Singapore, Busan, Johor, etc.).
   - *Public Status:* Delayed summary tables viewable; historical bulk daily download requires paid subscription to LME Data Services.
3. **LME Off-Warrant Stocks (Monthly):**
   - *Fields:* Metal stored in LME-registered facilities under non-warranted contracts.
   - *Frequency:* Monthly with a 1-month reporting lag.
   - *Usability for MVP:* Informative background metric, not suitable for daily/weekly quantitative signals.

### C. SHFE Data Capabilities
- **Daily Warehouse Warrant Data:** Published daily by SHFE at 15:30 Beijing time. Free HTML/CSV.
- **Weekly Warehouse Stock:** Published every Friday at 16:00 Beijing time. Tracks designated delivery warehouses in Shanghai, Jiangsu, Zhejiang, and Guangdong.
- **Daily Member Position Rankings:**
  - *Reality:* SHFE reports the Top 20 Member Futures Brokers (e.g., CITIC Futures, Guotai Junan) ranked by volume and Long/Short open contracts.
  - *Critical Distinction:* **These are broker clearing totals, NOT beneficial-owner categories.** A broker's Long total combines retail speculators, commercial miners, and hedgers. **SHFE member rankings cannot mathematically be equated with CFTC Managed Money.**

### D. Yangshan Copper Premium & Proxy Validation
- **What Yangshan Premium Measures:** The dollar-denominated cash surcharge (\$30–\$120/tonne) paid above the LME cash price to clear bonded imported cathode into Shanghai. It is the purest gauge of spot physical tightness in China.
- **The SHFE/LME Import Parity Proxy Formulation:**
  $$\text{Import Parity Ratio} = \frac{\text{SHFE Copper Price (RMB/t)} / (1 + \text{VAT}_{13\%})}{\text{LME Copper Cash Price (USD/t)} \times \text{USD/CNY Exchange Rate}}$$
- **Correction:** We searched the entire workspace for an independent, vendor-sourced Yangshan time-series. **No empirical Yangshan dataset exists locally.** Therefore, asserting a ">90% correlation" is scientifically invalid. The ratio reflects currency arbitrage and tax differences in addition to physical premiums.
- **Mandated Standard:** It must strictly be identified in the platform as `SHFE_LME_Import_Parity_Proxy` (unit: dimensionless ratio).

### E. Futures Price Data Hygiene
Detailed inspection of `data/prices/hg_f.parquet`, `si_f.parquet`, and `pl_f.parquet`:
- **Date Span in Local Files:** `2021-10-18` to `2026-10-30` (1,268 trading records).
- **Date Span in Adjacent Daily Store:** `2000-01-03` to `2026-10-20` (6,564 valid price bars for Copper).
- **Missing Observations:** 0 nulls in OHLC for Copper.
- **Volume Quality:** 7 zero-volume bars in Copper (`HG=F`), 47 in Silver (`SI=F`), 488 in Platinum (`PL=F` — indicating Platinum liquidity in standard contracts is thinner).
- **Continuous Methodology:** The underlying continuous series is back-adjusted front-month roll from Yahoo Finance (`HG=F`). It reflects trading session close, **not CME official preliminary/final clearing house settlement bulletins**.
- **Research Usability:** Completely sufficient for multi-week momentum, correlation, and directional return studies; not sufficient for tick-level execution or intraday market-making simulations.

### F. Fundamental Supply-Demand Validation
- **ICSG Copper Coverage:** Contains 14 canonical records spanning 2018–2025.
- **Publication Lag Analysis:** The ICSG 2024 annual figures carry `available_at = 2026-04-23`.
- **Temporal Integrity Rule:** Any forward-fill must only start **on or after** `available_at` (April 2026) to prevent lookahead bias. The model must not project 2024 supply figures into trading dates in early 2024.

---

## 3. TEMPORAL ALIGNMENT MATRIX

To prevent look-ahead bias and spurious causality, all datasets must adhere to explicit release timestamps:

| Dataset | Metric / Field | Observation Frequency | Observation Snapshot Cutoff | Public Release Timestamp | Publication Lag | Permissible Return Anchor |
|---|---|:---:|---|---|:---:|---|
| **CFTC Disaggregated COT** | Managed Money Net % OI | Weekly | Tuesday 17:00 EST | Friday 15:30 EST | 3 Trading Days | Monday Open / Friday Close Forward |
| **LME CoP** | Investment Funds Net | Weekly | Friday 17:00 London | Tuesday 13:00 London | 2 Trading Days | Wednesday Open Forward |
| **LME Stock Movement** | Closing Stocks, Cancelled % | Daily | Daily 08:00 London | Daily 09:00 London | Same Day (1 hour) | T+0 Close / T+1 Open |
| **SHFE Weekly Stock** | Deliverable Inventories | Weekly | Friday 15:00 Beijing | Friday 16:00 Beijing | Same Day (1 hour) | Next Week Open Forward |
| **COMEX Warehouse Stock** | Registered / Eligible | Daily | Daily 15:00 EST | Daily 16:30 EST | Same Day | T+1 Open Forward |
| **ICSG World Balance** | Refined Balance (kt) | Monthly / Annual | Monthly end | T+60 to T+90 Days | 2–3 Months | Post-Release Date Forward |
| **FRED Real Yield (DFII10)** | US 10Y Real Rate (%) | Daily | Daily Close | T+1 08:00 EST | 1 Day | T+1 Forward |
| **CME Copper (`HG=F`)** | Continuous Daily OHLCV | Daily | Daily 17:00 EST | Daily 17:30 EST | Real-time / EOD | Baseline Time-Series |

---

## 4. COPPER MVP READINESS ASSESSMENT

| Dataset Candidate | Audit Classification | Empirical Evidence / Rationale | Recommendation for MVP |
|---|:---:|---|:---:|
| **1. COMEX Copper Price (`HG=F`)** | **Verified & Usable** | 6,564 clean daily bars in feature store (2000–2026). Zero OHLC nulls. | **INCLUDE (Core Anchor)** |
| **2. CFTC Disaggregated COT (085692)** | **Verified & Usable** | 100% complete 2018–2026 weekly series in local Parquet. | **INCLUDE (Core Positioning)** |
| **3. FRED US 10Y Real Yield (`DFII10`)** | **Verified & Usable** | Complete daily time-series ready in `02_raw/macro_cross/`. | **INCLUDE (Macro Liquidity)** |
| **4. FRED Broad USD Index (`DTWEXBGS`)** | **Verified & Usable** | Complete daily series ready in `02_raw/macro_cross/`. | **INCLUDE (Currency Driver)** |
| **5. ICSG Copper World Balance** | **Available (Strict Rules)** | Canonical store contains 2018–2025; requires publication-aware dating. | **INCLUDE (Structural Regime)** |
| **6. COMEX Warehouse Copper Stocks** | **Available in Workspace** | Daily records exist in Bronze layer; easy daily ingestion pipeline. | **INCLUDE (US Physical Stock)** |
| **7. LME Daily Stock Movement Summary** | **Feasible (Public Free)** | Free daily figures available on LME.com; low technical complexity. | **INCLUDE (Global Physical Stock)** |
| **8. LME Commitments of Position (CoP)** | **Feasible with Restrictions** | Excel downloads available from 2018; requires pipeline and license respect. | **INCLUDE (European Positioning)** |
| **9. SHFE Weekly Copper Inventory** | **Feasible (Public Free)** | Weekly Friday reports on shfe.com.cn; simple tabular scrape. | **INCLUDE (China Physical Stock)** |
| **10. SHFE/LME Import Parity Proxy** | **Feasible Mathematical Model** | Computed from SHFE Copper / (LME Cash * USDCNY * 1.13). | **INCLUDE (Labeled as Proxy)** |
| **11. Actual Yangshan Copper Premium** | **Requires Paid Access / Vendor** | No historical dataset currently exists locally. | **DEFER (Until Source Procured)** |
| **12. SHFE Member Position Rankings** | **Not Recommended for MVP** | Broker-level clearing totals; non-comparable to fund positioning. | **DEFER (Methodological Barrier)** |
| **13. Real-Time Tick LME Ring Data** | **Requires Paid Access ($20k+)** | Prohibitive commercial exchange licensing fee. | **EXCLUDE (Delayed EOD is Sufficient)** |

---

## 5. THREE FORMAL MVP PACKAGES

### Package A: Immediate Zero-Risk MVP (Deployable Today)
*Requires 0 external downloads and 0 API scrapers. Uses 100% verified local data.*
1. COMEX Copper Daily Continuous Futures (`HG=F`).
2. CFTC Disaggregated Copper COT (085692).
3. FRED 10Y Real Yield (`DFII10`) & Nominal Yield (`DGS10`).
4. FRED Trade-Weighted Dollar Index (`DTWEXBGS`).
5. ICSG Canonical S&D Annual/Monthly Balance (`fundamental_latest.parquet` with publication-lag rule).

### Package B: Recommended Global Intelligence MVP (Targeted Phase 1)
*Combines Package A with 4 high-reliability, free public datasets.*
1. All elements of Package A.
2. COMEX Copper Daily Warehouse Stocks (Registered vs Eligible).
3. LME Copper Daily Total Stocks & Cancelled Warrants Ratio.
4. SHFE Weekly Deliverable Warehouse Stockpile.
5. LME Commitments of Position (CoP - Investment Funds Net Positioning).
6. Mathematical `SHFE_LME_Import_Parity_Proxy`.

### Package C: Institutional Expanded Platform (Future Licensed Expansion)
*Includes commercial proprietary feeds.*
1. All elements of Package B.
2. Vendor-sourced Historical Yangshan Copper Spot Premium (SMM / Fastmarkets).
3. Official LME Daily Closing Cash-to-3M Forward Spreads.
4. Shanghai Metals Market (SMM) Daily Cathode Inventories.

---

## 6. PHASE 0.5 SIGN-OFF & CRITERIA VERIFICATION

1. **All five major audit claims investigated and resolved:** YES. (LME CoP legal terms clarified, Yangshan proxy separated, Price continuous history verified, S&D lag rule established).
2. **Copper MVP package reassessed with clear inclusions/exclusions:** YES. (10 datasets approved, 3 deferred/excluded).
3. **Temporal alignment matrix generated:** YES. (Saved to `docs/audit/DATA_TEMPORAL_ALIGNMENT_MATRIX.csv`).
4. **Readiness matrix generated:** YES. (Saved to `docs/audit/COPPER_MVP_READINESS.csv`).
5. **Phase 1 scope defined and justified by empirical evidence:** YES.
