"""
COT DATA RESEARCH LAB — Module 8: Research Report Workspace & Reproducibility
Integrated with Commodity Price Behavior (Phase 11)
"""

import streamlit as st
import datetime
import json
from research_lab.price_engine import COT_PRICE_MARKET_REGISTRY

def render_reports(commodity_label, report_family_name, contract_code, market_df, price_df=None):
    st.title("📝 Quantitative Research Report Workspace")
    st.caption("Generate, document, and export reproducible institutional quantitative research briefs integrating COT positioning and commodity price behavior.")

    d_min = market_df['report_date'].min().strftime('%Y-%m-%d') if not market_df.empty else 'N/A'
    d_max = market_df['report_date'].max().strftime('%Y-%m-%d') if not market_df.empty else 'N/A'
    n_obs = len(market_df)

    p_meta = COT_PRICE_MARKET_REGISTRY.get(commodity_label, {
        "instrument": "Continuous Futures",
        "exchange": "COMEX / NYMEX",
        "price_unit": "USD",
        "roll_methodology": "Standard calendar roll",
        "source": "Market Data Lake"
    })

    with st.form("research_report_form"):
        st.subheader("1. Research Parameters & Identification")
        c1, c2 = st.columns(2)
        with c1:
            report_title = st.text_input("Research Title:", value=f"Quantitative Investigation of {commodity_label} Positioning & Price Relationship")
            research_question = st.text_area("Research Question:", value=f"Does extreme Managed Money positioning in {commodity_label} provide statistically significant lead-lag information regarding subsequent spot/futures price returns, and how robust is this across market regimes?")
        with c2:
            author = st.text_input("Lead Quantitative Researcher:", value="Institutional Quantitative Research Team")
            methodology_summary = st.text_area("Methodology Summary:", value="Lookahead-safe weekly frequency alignment (Friday publication-aware anchor), Newey-West HAC regression, multi-horizon Information Coefficient (IC 1W to 26W), and extreme event study (|Z| >= 2.0σ with first-crossing deduplication).")

        st.subheader("2. Empirical Observations & Findings")
        findings = st.text_area(
            "Empirical Findings Summary:",
            value=f"Empirical evaluation of {n_obs} weekly observations between {d_min} and {d_max} shows: (1) Lead-lag cross correlation peaks contemporaneously with strong backward decay, indicating trend-following positioning adjustments. (2) Forward returns following Extreme Long events (|Z| >= 2σ) display asymmetric performance conditioned on the broader price trend (uptrend continuation vs downtrend exhaustion). (3) Spearman Rank IC remains modest across 1W–4W horizons but increases over intermediate multi-month horizons."
        )

        st.subheader("3. Governance, Provenance & Limitations")
        limitations = st.text_area(
            "Research Limitations & Non-Trading Disclaimer:",
            value="Data is observed weekly with a 3-day reporting latency (Tuesday survey to Friday 15:30 ET publication). Extreme positioning episodes are finite in sample size. Correlation and event trajectories describe historical tendencies and do not constitute automated trading signals, execution rules, or capital allocation recommendations."
        )

        submitted = st.form_submit_button("🔨 Compile Research Report")

    # Generate Markdown export
    report_md = f"""# {report_title}
**Analyst / Organization:** {author} | **Date:** {datetime.date.today().strftime('%Y-%m-%d')}
**Target Commodity:** {commodity_label} (CFTC Code: `{contract_code}`)
**Report Classification:** {report_family_name} (Combined Futures & Options)
**Sample Window:** {d_min} to {d_max} ({n_obs} weekly observations)

---

### 1. Market Mapping & Price Data Provenance
- **Exchange:** {p_meta.get('exchange', 'COMEX')}
- **Underlying Instrument:** {p_meta.get('instrument', 'Continuous Futures')}
- **Pricing Unit:** {p_meta.get('price_unit', 'USD')}
- **Roll Methodology:** {p_meta.get('roll_methodology', 'Volume/OI active roll')}
- **Data Source:** {p_meta.get('source', 'Local Verified Lakehouse')}
- **Alignment Anchor:** Friday 15:30 ET publication close (guaranteeing zero look-ahead bias)

### 2. Research Hypothesis & Core Question
{research_question}

### 3. Quantitative Methodology
{methodology_summary}

### 4. Empirical Statistical Findings
{findings}

### 5. Research Governance & Known Limitations
{limitations}

### 6. Reproducibility Configuration
```json
{{
    "commodity": "{commodity_label}",
    "cftc_contract_code": "{contract_code}",
    "report_family": "{report_family_name}",
    "sample_start": "{d_min}",
    "sample_end": "{d_max}",
    "observation_count": {n_obs},
    "instrument": "{p_meta.get('instrument', 'Continuous Futures')}",
    "generated_at": "{datetime.datetime.now().isoformat()}",
    "compliance_tier": "Strictly Non-Trading Analytical Workstation"
}}
```
"""

    st.subheader("Generated Research Brief (Markdown Preview)")
    st.markdown(report_md)

    st.download_button(
        label="📥 Download Research Report (.md)",
        data=report_md,
        file_name=f"COT_Price_Research_Report_{commodity_label}_{datetime.date.today().strftime('%Y%m%d')}.md",
        mime="text/markdown"
    )
