"""
COT DATA RESEARCH LAB — Module 9: Data Center & Export Hub
Permits interactive preview, filtering, and direct CSV / Parquet downloading of:
1. Curated Weekly COT Market Data (Active Commodity)
2. Daily / Weekly Physical Commodity Settlement Prices
3. Aligned Multi-Variable Research Dataset (Positions + Prices + Flows + Metrics)
4. Full COT Historical Archives (Disaggregated & Legacy)
"""

import streamlit as st
import pandas as pd
import io
from research_lab.metrics_engine import compute_trader_metrics, compute_position_decomposition
from research_lab.price_engine import align_cot_and_price, COT_PRICE_MARKET_REGISTRY

def render_data_center(market_df, report_family_name, commodity_label, price_df, df_disagg, df_tff):
    st.title(f"📥 Data Center & Export Hub — {commodity_label}")
    st.caption("Directly inspect, customize, and export curated datasets in CSV or Parquet formats.")

    st.markdown("""
    The Data Center empowers researchers to inspect raw and processed time-series, customize feature subsets, and export research-ready datasets for external modeling in Python, R, or Excel.
    """)

    tabs = st.tabs([
        "📊 1. Weekly COT Positioning (Active Market)",
        "📈 2. Commodity Futures Settlement Prices",
        "🧪 3. Aligned Multi-Horizon Research Dataset",
        "📦 4. Comprehensive Historical Archives"
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1: ACTIVE MARKET COT DATA
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[0]:
        st.subheader(f"1. COT Positioning Time-Series: {commodity_label} ({report_family_name})")
        st.caption("Complete weekly positioning reports decomposed across participant cohorts.")

        if market_df.empty:
            st.warning("No data available for the active selection.")
        else:
            m_metrics = compute_trader_metrics(market_df, report_family_name)
            
            c_f1, c_f2 = st.columns([2, 1])
            with c_f1:
                export_cols = st.multiselect(
                    "Select Columns to Export (Defaults to core quant features):",
                    options=list(m_metrics.columns),
                    default=[c for c in [
                        'report_date', 'contract_code', 'market_name', 'Open_Interest_All',
                        'primary_spec_net', 'primary_commercial_net', 'managed_money_net_pct_oi',
                        'prod_merc_net_pct_oi', 'swap_net_pct_oi', 'non_rept_net_pct_oi'
                    ] if c in m_metrics.columns]
                )
            with c_f2:
                max_preview_rows = st.number_input("Preview Rows:", min_value=5, max_value=500, value=15, key="cot_prev_rows")

            if not export_cols:
                export_cols = list(m_metrics.columns)

            subset_df = m_metrics[export_cols].sort_values('report_date', ascending=False)
            
            st.markdown(f"**Data Preview ({len(subset_df)} total observations):**")
            st.dataframe(subset_df.head(max_preview_rows), use_container_width=True)

            cd1, cd2 = st.columns(2)
            with cd1:
                csv_bytes = subset_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"⬇️ Download CSV ({commodity_label}_COT.csv)",
                    data=csv_bytes,
                    file_name=f"{commodity_label.lower().replace(' ', '_')}_{report_family_name.lower().replace(' ', '_')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="• Format: Standard Comma-Separated Values.\n• Compatibility: Microsoft Excel, Google Sheets, Pandas, R."
                )
            with cd2:
                buffer = io.BytesIO()
                subset_df.to_parquet(buffer, index=False)
                st.download_button(
                    label=f"⬇️ Download Parquet ({commodity_label}_COT.parquet)",
                    data=buffer.getvalue(),
                    file_name=f"{commodity_label.lower().replace(' ', '_')}_{report_family_name.lower().replace(' ', '_')}.parquet",
                    mime="application/octet-stream",
                    use_container_width=True,
                    help="• Format: Apache Parquet (snappy compression).\n• Purpose: High-performance columnar storage with strict schema typing."
                )

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2: COMMODITY PRICE DATA
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[1]:
        st.subheader(f"2. Daily & Weekly Physical Futures Settlement Prices")
        st.caption("Continuous daily settlement price time-series linked to active physical commodity contracts.")

        if commodity_label in ["Copper", "Silver", "Platinum"] and price_df is not None and not price_df.empty:
            p_code = {"Copper": "hg_f", "Silver": "si_f", "Platinum": "pl_f"}.get(commodity_label)
            p_sub = price_df[price_df['commodity'] == p_code].copy() if 'commodity' in price_df.columns else price_df.copy()
            
            if p_sub.empty:
                p_sub = price_df.copy()

            p_sub = p_sub.sort_values('date', ascending=False) if 'date' in p_sub.columns else p_sub

            st.markdown(f"**Price History Preview for {commodity_label} ({len(p_sub):,} trading days):**")
            st.dataframe(p_sub.head(15), use_container_width=True)

            cd_p1, cd_p2 = st.columns(2)
            with cd_p1:
                csv_p_bytes = p_sub.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"⬇️ Download Price History (CSV)",
                    data=csv_p_bytes,
                    file_name=f"{commodity_label.lower()}_futures_daily.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="• Format: CSV continuous daily settlement prices."
                )
            with cd_p2:
                buf_p = io.BytesIO()
                p_sub.to_parquet(buf_p, index=False)
                st.download_button(
                    label=f"⬇️ Download Price History (Parquet)",
                    data=buf_p.getvalue(),
                    file_name=f"{commodity_label.lower()}_futures_daily.parquet",
                    mime="application/octet-stream",
                    use_container_width=True,
                    help="• Format: Compressed Apache Parquet."
                )
        else:
            st.info(f"Verified continuous daily settlement prices are currently curated for Copper, Silver, and Platinum.")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3: ALIGNED RESEARCH DATASET
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[2]:
        st.subheader("3. Integrated Multi-Horizon Research Dataset")
        st.caption("Aligned Positioning, Forward Price Returns (1W, 2W, 4W, 8W, 13W, 26W), Flow Drivers, and Z-Scores.")

        if commodity_label in ["Copper", "Silver", "Platinum"]:
            m_metrics = compute_trader_metrics(market_df, report_family_name)
            spec_prefix = "M_Money" if "Disaggregated" in report_family_name else "Lev_Money"
            m_metrics = compute_position_decomposition(m_metrics, category_prefix=spec_prefix)

            conv = st.radio(
                "Price Alignment Convention:",
                ["Publication-Aware (Friday Close Anchor - Zero Lookahead)", "Tuesday Survey Close (Contemporaneous Benchmark)"],
                horizontal=True
            )
            c_code = "publication_aware" if "Publication-Aware" in conv else "tuesday_close"

            aligned_data = align_cot_and_price(m_metrics, commodity_label, convention=c_code)

            if not aligned_data.empty:
                st.markdown(f"**Preview Aligned Research Table ({len(aligned_data)} aligned weekly periods):**")
                st.dataframe(aligned_data.sort_values('report_date', ascending=False).head(15), use_container_width=True)

                ca1, ca2 = st.columns(2)
                with ca1:
                    csv_a = aligned_data.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=f"⬇️ Download Aligned Dataset (CSV)",
                        data=csv_a,
                        file_name=f"{commodity_label.lower()}_aligned_research_dataset.csv",
                        mime="text/csv",
                        use_container_width=True,
                        help="• Pre-computed features: Forward returns, flow decomposition, rolling z-scores, aligned dates."
                    )
                with ca2:
                    buf_a = io.BytesIO()
                    aligned_data.to_parquet(buf_a, index=False)
                    st.download_button(
                        label=f"⬇️ Download Aligned Dataset (Parquet)",
                        data=buf_a.getvalue(),
                        file_name=f"{commodity_label.lower()}_aligned_research_dataset.parquet",
                        mime="application/octet-stream",
                        use_container_width=True,
                        help="• Ready for algorithmic research in Python, Statsmodels, and Scikit-Learn."
                    )
        else:
            st.info("Price alignment is active for benchmark physical commodities (Copper, Silver, Platinum).")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 4: COMPLETE ARCHIVES
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[3]:
        st.subheader("4. Full Historical Archives (Complete CFTC Database)")
        st.caption("Download comprehensive multi-decade positioning records across all global commodity and financial contracts.")

        col_arc1, col_arc2 = st.columns(2)

        with col_arc1:
            st.markdown("""
            #### 📦 Disaggregated COT Full Archive (2018 – 2026)
            - **Scope:** Complete disaggregated breakdown across Agriculture, Energy, and Metals.
            - **Size:** ~24 MB (Compressed Apache Parquet format).
            """)
            if df_disagg is not None and not df_disagg.empty:
                buf_dis = io.BytesIO()
                df_disagg.to_parquet(buf_dis, index=False)
                st.download_button(
                    label="⬇️ Download Full Disaggregated COT (Parquet)",
                    data=buf_dis.getvalue(),
                    file_name="cot_disagg_full_archive.parquet",
                    mime="application/octet-stream",
                    use_container_width=True
                )

        with col_arc2:
            st.markdown("""
            #### 📦 Financial Futures (TFF) Full Archive
            - **Scope:** Complete financial futures breakdown (Equities, Interest Rates, FX, Treasuries).
            - **Size:** Lightweight optimized Parquet format.
            """)
            if df_tff is not None and not df_tff.empty:
                buf_tff = io.BytesIO()
                df_tff.to_parquet(buf_tff, index=False)
                st.download_button(
                    label="⬇️ Download Full TFF Archive (Parquet)",
                    data=buf_tff.getvalue(),
                    file_name="cot_tff_full_archive.parquet",
                    mime="application/octet-stream",
                    use_container_width=True
                )
