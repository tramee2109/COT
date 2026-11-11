"""
COT DATA RESEARCH LAB / GLOBAL COMMODITY INTELLIGENCE — Module 10: Copper Research Foundation
Institutional Quantitative Workstation for COMEX Copper (Code: 085692).
Connecting Futures Price, CFTC Positioning, Macro Liquidity (Real Yields & Broad USD), and ICSG Physical Fundamentals.
Strictly non-trading, analytical & educational research platform.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from research_lab.config import COLORS
from research_lab.metrics_engine import compute_trader_metrics, compute_position_decomposition
from research_lab.copper_foundation_service import (
    load_canonical_fundamentals,
    load_fred_macro_series,
    align_copper_price_cot_macro_fundamentals
)

def render_copper_foundation(market_df, report_family_name, commodity_label, price_df):
    st.title("🏛️ Copper Research Foundation (Global Intelligence Platform)")
    st.caption("Comprehensive multi-layer quantitative integration for COMEX Copper (Code: 085692).")

    # Governance Notice
    st.info("""
    ℹ️ **Institutional Research Framework:** This module bridges COMEX continuous futures prices with CFTC speculative positioning,
    official Federal Reserve (FRED) macro factors, and International Copper Study Group (ICSG) physical balances using publication-aware alignment.
    Strictly non-trading; no automated signals or execution.
    """)

    # Verify Copper context
    if commodity_label != "Copper" and "085692" not in str(market_df.get("CFTC_Contract_Market_Code", [""])[0]):
        st.warning(f"⚠️ Currently active market is '{commodity_label}'. Please switch to **Copper** in the sidebar to activate the Copper Research Foundation.")
        return

    # Calculate canonical trader metrics for the selected report family (DEF-1.1-01 fix)
    market_df = compute_trader_metrics(market_df, report_family_name)

    # Data Alignment with Zero Lookahead
    with st.spinner("Constructing Publication-Aware Copper Multi-Layer Research Dataset..."):
        aligned_df = align_copper_price_cot_macro_fundamentals(market_df, price_df, convention="publication_aware")

    if aligned_df.empty:
        st.error("Failed to construct aligned Copper research dataset. Verify price and COT files.")
        return

    # ─────────────────────────────────────────────────────────────────────────
    # SUB-MODULE TABS
    # ─────────────────────────────────────────────────────────────────────────
    tabs = st.tabs([
        "🌐 1. Market Overview & Dashboard",
        "📈 2. Price & Positioning Explorer",
        "⚡ 3. Positioning Dynamics & Extremes",
        "💵 4. Macro & Copper Dynamics (FRED)",
        "🏭 5. Physical Supply-Demand (ICSG)",
        "🧪 6. Multi-Factor Relationship Lab",
        "📋 7. Research Briefing Workspace"
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1: MARKET OVERVIEW
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[0]:
        st.subheader("1. Copper Multi-Layer Market Overview")
        st.caption("Real-time telemetry across Price, Speculative Flows, Macro Drivers, and Physical Balance.")

        latest = aligned_df.iloc[-1]
        prev = aligned_df.iloc[-2]

        c_p = latest.get("price", np.nan)
        c_p_prev = prev.get("price", np.nan)
        p_delta_pct = ((c_p - c_p_prev) / c_p_prev * 100.0) if pd.notna(c_p) and pd.notna(c_p_prev) and c_p_prev > 0 else np.nan

        mm_net = latest.get("managed_money_net", latest.get("M_Money_Positions_Long_All", 0) - latest.get("M_Money_Positions_Short_All", 0))
        mm_net_prev = prev.get("managed_money_net", prev.get("M_Money_Positions_Long_All", 0) - prev.get("M_Money_Positions_Short_All", 0))
        mm_net_pct = latest.get("managed_money_net_pct_oi", (mm_net / latest.get("Open_Interest_All", 1) * 100.0))

        prod_net = latest.get("prod_merc_net", latest.get("Prod_Merc_Positions_Long_All", 0) - latest.get("Prod_Merc_Positions_Short_All", 0))
        prod_net_pct = latest.get("prod_merc_net_pct_oi", (prod_net / latest.get("Open_Interest_All", 1) * 100.0))

        ry = latest.get("us_10y_real_yield", np.nan)
        ry_prev = prev.get("us_10y_real_yield", np.nan)

        dxy = latest.get("nominal_broad_usd_index", np.nan)
        dxy_prev = prev.get("nominal_broad_usd_index", np.nan)

        bal_kt = latest.get("icsg_apparent_balance_kt", np.nan)

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric(
                "COMEX Copper Price", f"${c_p:.4f} / lb" if pd.notna(c_p) else "N/A",
                delta=f"{p_delta_pct:+.2f}% WoW" if pd.notna(p_delta_pct) else None,
                help="- **Source:** Continuous front-month futures (Yahoo Finance: `HG=F`).\n\n- **Note:** Represents daily session closing price, not official clearing settlement bulletin."
            )
        with k2:
            st.metric(
                "Managed Money Net", f"{mm_net:+,.0f} ctrs",
                delta=f"{mm_net - mm_net_prev:+,.0f} WoW ({mm_net_pct:+.1f}% of OI)",
                help="- **Formula:** Gross Long - Gross Short for Managed Money.\n\n- **Purpose:** Primary gauge of hedge fund / CTA trend momentum commitment."
            )
        with k3:
            st.metric(
                "Producer / Merchant Net", f"{prod_net:+,.0f} ctrs",
                delta=f"{prod_net_pct:+.1f}% of OI",
                help="- **Formula:** Commercial physical producer Gross Long - Gross Short.\n\n- **Purpose:** Measures commercial forward sales and hedging intensity."
            )
        with k4:
            st.metric(
                "US 10Y Real Yield (FRED)", f"{ry:.2f}%" if pd.notna(ry) else "N/A",
                delta=f"{ry - ry_prev:+.2f}% WoW" if (pd.notna(ry) and pd.notna(ry_prev)) else None,
                help="- **Series:** FRED `DFII10` (10-Year Treasury Inflation-Indexed Security).\n\n- **Purpose:** Real capital opportunity cost driving global commodity investment."
            )

        k5, k6, k7, k8 = st.columns(4)
        with k5:
            st.metric(
                "Broad USD Index (FRED)", f"{dxy:.2f}" if pd.notna(dxy) else "N/A",
                delta=f"{dxy - dxy_prev:+.2f} WoW" if (pd.notna(dxy) and pd.notna(dxy_prev)) else None,
                help="- **Series:** FRED `DTWEXBGS` (Trade-Weighted Nominal Broad U.S. Dollar Index).\n\n- **Note:** Weighted against emerging & developed trade partners. NOT ICE DXY."
            )
        with k6:
            st.metric(
                "ICSG Apparent Balance", f"{bal_kt:+,.0f} kt" if pd.notna(bal_kt) else "N/A",
                delta="Annualized Estimate",
                help="- **Formula:** ICSG Refined Production - Refined Usage (Thousand Metric Tons).\n\n- **Publication Lag:** Strictly respects official release date."
            )
        with k7:
            tot_oi = latest.get("Open_Interest_All", np.nan)
            st.metric(
                "Market Open Interest", f"{tot_oi:,.0f} ctrs" if pd.notna(tot_oi) else "N/A",
                delta=f"{tot_oi - prev.get('Open_Interest_All', 0):+,.0f} WoW"
            )
        with k8:
            asof_date = latest["report_date"].strftime("%Y-%m-%d")
            st.metric("As-Of Date", asof_date, delta="Publication Aligned")

        st.markdown(f"""
        <div style="background: rgba(22, 28, 40, 0.7); border: 1px solid #1f2737; border-radius: 6px; padding: 12px 16px; margin-top: 15px; font-size: 13px;">
            <b>Telemetry Provenance Summary:</b> &nbsp;•&nbsp; 
            Price Anchor: <code>COMEX Continuous Front-Month (HG=F)</code> &nbsp;•&nbsp; 
            COT Standard: <code>CFTC Disaggregated Combined (085692)</code> &nbsp;•&nbsp; 
            Macro Sources: <code>Federal Reserve Economic Data (FRED DFII10 / DTWEXBGS)</code> &nbsp;•&nbsp; 
            Fundamentals: <code>International Copper Study Group (ICSG Selected Stats)</code> &nbsp;•&nbsp; 
            Current Date Anchor: <code>{asof_date} (Friday Release Cutoff)</code>
        </div>
        """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2: PRICE & POSITIONING EXPLORER
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[1]:
        st.subheader("2. Price & Positioning Interactive Explorer")
        st.caption("3-Panel synchronized time-series tracking price trajectories alongside cohort positioning and weekly flows.")

        fig_exp = make_subplots(
            rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
            row_heights=[0.45, 0.35, 0.20],
            subplot_titles=[
                "Panel A: COMEX Copper Price ($/lb)",
                "Panel B: Net Positioning by Trader Cohort (Contracts)",
                "Panel C: Net Positioning as % of Total Open Interest"
            ]
        )

        # Panel A: Price
        fig_exp.add_trace(go.Scatter(
            x=aligned_df['report_date'], y=aligned_df['price'], mode='lines',
            name='Copper Price ($/lb)', line=dict(color='#fbc531', width=2.5)
        ), row=1, col=1)

        # Panel B: Positioning in Contracts
        fig_exp.add_trace(go.Scatter(
            x=aligned_df['report_date'], y=aligned_df['primary_spec_net'], mode='lines',
            name='Managed Money Net', line=dict(color=COLORS['managed_money'], width=2)
        ), row=2, col=1)
        fig_exp.add_trace(go.Scatter(
            x=aligned_df['report_date'], y=aligned_df['primary_commercial_net'], mode='lines',
            name='Producer / Merchant Net', line=dict(color=COLORS['prod_merc'], width=2)
        ), row=2, col=1)
        if 'swap_net' in aligned_df.columns:
            fig_exp.add_trace(go.Scatter(
                x=aligned_df['report_date'], y=aligned_df['swap_net'], mode='lines',
                name='Swap Dealer Net', line=dict(color=COLORS['swap_dealer'], width=1.5, dash='dot')
            ), row=2, col=1)
        fig_exp.add_hline(y=0, line_dash='dash', line_color='gray', row=2, col=1)

        # Panel C: Net % of Open Interest
        if 'managed_money_net_pct_oi' in aligned_df.columns:
            fig_exp.add_trace(go.Scatter(
                x=aligned_df['report_date'], y=aligned_df['managed_money_net_pct_oi'], mode='lines',
                name='Managed Money % OI', line=dict(color=COLORS['managed_money'], width=1.8)
            ), row=3, col=1)
        if 'prod_merc_net_pct_oi' in aligned_df.columns:
            fig_exp.add_trace(go.Scatter(
                x=aligned_df['report_date'], y=aligned_df['prod_merc_net_pct_oi'], mode='lines',
                name='Producer % OI', line=dict(color=COLORS['prod_merc'], width=1.8)
            ), row=3, col=1)
        fig_exp.add_hline(y=0, line_dash='dash', line_color='gray', row=3, col=1)

        fig_exp.update_layout(
            template='plotly_dark', height=650,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation='h', y=1.05, x=0)
        )
        fig_exp.update_yaxes(title_text="Price ($/lb)", row=1, col=1)
        fig_exp.update_yaxes(title_text="Net Contracts", row=2, col=1)
        fig_exp.update_yaxes(title_text="% of Total OI", row=3, col=1)
        st.plotly_chart(fig_exp, use_container_width=True)

        with st.expander("💡 Analytical Guidance: Interpreting Lead-Lag Relationships", expanded=False):
            st.markdown("""
            - **Trend Continuation:** When Copper breaks out to new price highs with expanding Managed Money Longs and deepening Producer Shorts, speculative momentum confirms the physical rally.
            - **Divergence Exhaustion:** When Copper reaches fresh price highs but Managed Money Net % OI peaks and turns downward, upside liquidity is eroding.
            - **Commercial Support:** Deeply negative Producer Net positioning indicates aggressive forward selling; conversely, when Producer Net rises toward neutral, miners are withholding sales due to low prices, establishing structural floors.
            """)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3: POSITIONING DYNAMICS & EXTREMES
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[2]:
        st.subheader("3. Speculative Positioning Dynamics & Historical Lookback Extremes")
        st.caption("Standardized Z-Score and Percentile rankings across 52W, 156W (3Y), and 260W (5Y) lookbacks.")

        c_w1, c_w2 = st.columns([1, 2])
        with c_w1:
            sel_window = st.selectbox("Historical Lookback Window:", [52, 104, 156, 260], format_func=lambda x: f"{x} Weeks ({round(x/52, 1)} Years)", index=0)

        # Dynamic rolling calculations
        roll_mean = aligned_df['primary_spec_net'].rolling(sel_window).mean()
        roll_std = aligned_df['primary_spec_net'].rolling(sel_window).std()
        aligned_df['dyn_zscore'] = (aligned_df['primary_spec_net'] - roll_mean) / roll_std

        roll_min = aligned_df['primary_spec_net'].rolling(sel_window).min()
        roll_max = aligned_df['primary_spec_net'].rolling(sel_window).max()
        aligned_df['dyn_percentile'] = (aligned_df['primary_spec_net'] - roll_min) / (roll_max - roll_min) * 100.0

        fig_dyn = make_subplots(
            rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06,
            row_heights=[0.5, 0.5],
            subplot_titles=[
                f"Speculative Net Rolling Z-Score ({sel_window}W)",
                f"Speculative Net Percentile Rank ({sel_window}W)"
            ]
        )
        fig_dyn.add_trace(go.Scatter(
            x=aligned_df['report_date'], y=aligned_df['dyn_zscore'], mode='lines',
            name='Z-Score (σ)', line=dict(color=COLORS['managed_money'], width=2)
        ), row=1, col=1)
        fig_dyn.add_hline(y=2.0, line_dash='dash', line_color='#eb4d4b', annotation_text="+2σ (Crowded Long)", row=1, col=1)
        fig_dyn.add_hline(y=-2.0, line_dash='dash', line_color='#2ecc71', annotation_text="-2σ (Exhaustion Short)", row=1, col=1)
        fig_dyn.add_hline(y=0, line_dash='solid', line_color='gray', row=1, col=1)

        fig_dyn.add_trace(go.Scatter(
            x=aligned_df['report_date'], y=aligned_df['dyn_percentile'], mode='lines',
            name='Percentile (%)', line=dict(color='#00d2d3', width=2)
        ), row=2, col=1)
        fig_dyn.add_hline(y=90.0, line_dash='dash', line_color='#eb4d4b', annotation_text="90th Pct", row=2, col=1)
        fig_dyn.add_hline(y=10.0, line_dash='dash', line_color='#2ecc71', annotation_text="10th Pct", row=2, col=1)
        fig_dyn.add_hline(y=50.0, line_dash='solid', line_color='gray', row=2, col=1)

        fig_dyn.update_layout(template='plotly_dark', height=480, margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
        st.plotly_chart(fig_dyn, use_container_width=True)

        curr_z = aligned_df['dyn_zscore'].iloc[-1]
        curr_pct = aligned_df['dyn_percentile'].iloc[-1]
        st.markdown(f"""
        **Statistical Tail Risk Status ({sel_window}W Window):**
        - **Rolling Z-Score:** `{curr_z:+.2f} σ` &nbsp;|&nbsp; **Rolling Percentile:** `{curr_pct:.1f}%`
        - **Diagnosis:** {'🔴 Extreme Bullish Crowding (Z >= +2.0σ)' if curr_z >= 2.0 else '🟢 Extreme Bearish Exhaustion (Z <= -2.0σ)' if curr_z <= -2.0 else '⚪ Normal Liquidity Corridor (|Z| < 2.0σ)'}
        """)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 4: MACRO & COPPER RELATIONSHIP
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[3]:
        st.subheader("4. Macro Driver Interactions: Real Yields & Broad USD")
        st.caption("Evaluates Copper price sensitivity to global capital costs and trade-weighted currency regimes.")

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            # Copper vs US 10Y Real Yield
            fig_ry = make_subplots(specs=[[{"secondary_y": True}]])
            fig_ry.add_trace(go.Scatter(
                x=aligned_df['report_date'], y=aligned_df['price'], mode='lines',
                name='Copper Price ($/lb)', line=dict(color='#fbc531', width=2)
            ), secondary_y=False)
            fig_ry.add_trace(go.Scatter(
                x=aligned_df['report_date'], y=aligned_df['us_10y_real_yield'], mode='lines',
                name='US 10Y Real Yield (%)', line=dict(color='#ff7675', width=1.8, dash='dot')
            ), secondary_y=True)
            fig_ry.update_layout(template='plotly_dark', height=360, margin=dict(l=20, r=20, t=30, b=20), title="Copper Price vs US 10Y Real Yield (FRED)")
            fig_ry.update_yaxes(title_text="Copper ($/lb)", secondary_y=False)
            fig_ry.update_yaxes(title_text="Real Yield (%)", secondary_y=True, showgrid=False)
            st.plotly_chart(fig_ry, use_container_width=True)

        with col_m2:
            # Copper vs Nominal Broad USD Index
            fig_dxy = make_subplots(specs=[[{"secondary_y": True}]])
            fig_dxy.add_trace(go.Scatter(
                x=aligned_df['report_date'], y=aligned_df['price'], mode='lines',
                name='Copper Price ($/lb)', line=dict(color='#fbc531', width=2)
            ), secondary_y=False)
            fig_dxy.add_trace(go.Scatter(
                x=aligned_df['report_date'], y=aligned_df['nominal_broad_usd_index'], mode='lines',
                name='Broad USD Index (FRED)', line=dict(color='#74b9ff', width=1.8, dash='dash')
            ), secondary_y=True)
            fig_dxy.update_layout(template='plotly_dark', height=360, margin=dict(l=20, r=20, t=30, b=20), title="Copper Price vs Nominal Broad USD Index")
            fig_dxy.update_yaxes(title_text="Copper ($/lb)", secondary_y=False)
            fig_dxy.update_yaxes(title_text="Broad USD Index", secondary_y=True, showgrid=False)
            st.plotly_chart(fig_dxy, use_container_width=True)

        # Macro Correlations Table
        valid_macro = aligned_df[['price', 'weekly_price_return', 'us_10y_real_yield', 'nominal_broad_usd_index']].dropna()
        if len(valid_macro) > 20:
            ry_corr = valid_macro['price'].corr(valid_macro['us_10y_real_yield'])
            usd_corr = valid_macro['price'].corr(valid_macro['nominal_broad_usd_index'])
            ry_ret_corr = valid_macro['weekly_price_return'].corr(valid_macro['us_10y_real_yield'].diff(1))
            usd_ret_corr = valid_macro['weekly_price_return'].corr(valid_macro['nominal_broad_usd_index'].diff(1))

            c_mc1, c_mc2, c_mc3, c_mc4 = st.columns(4)
            with c_mc1:
                st.metric("Price vs Real Yield (Level)", f"r = {ry_corr:+.3f}")
            with c_mc2:
                st.metric("Price vs Broad USD (Level)", f"r = {usd_corr:+.3f}")
            with c_mc3:
                st.metric("Return vs ΔReal Yield (Flow)", f"r = {ry_ret_corr:+.3f}")
            with c_mc4:
                st.metric("Return vs ΔBroad USD (Flow)", f"r = {usd_ret_corr:+.3f}")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 5: PHYSICAL SUPPLY-DEMAND (ICSG)
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[4]:
        st.subheader("5. Physical Fundamentals: ICSG World Refined Balance")
        st.caption("Annual and Monthly official figures from the International Copper Study Group. Preserving exact release lag.")

        canon_fund = load_canonical_fundamentals("Copper")
        if not canon_fund.empty:
            st.markdown("#### Official Canonical Dataset Table (ICSG & USGS)")
            st.dataframe(
                canon_fund[['period_year', 'metric', 'value_standardized', 'unit_standardized', 'publication_date', 'available_at', 'source_id', 'is_forecast']],
                use_container_width=True
            )

            # Bar chart of Production vs Usage
            piv_chart = canon_fund.pivot_table(index='period_year', columns='metric', values='value_standardized', aggfunc='last').reset_index()
            if 'refined_production' in piv_chart.columns and 'refined_usage' in piv_chart.columns:
                fig_fund = go.Figure()
                fig_fund.add_trace(go.Bar(
                    x=piv_chart['period_year'], y=piv_chart['refined_production'],
                    name='World Refined Production (kt)', marker_color='#2ed573'
                ))
                fig_fund.add_trace(go.Bar(
                    x=piv_chart['period_year'], y=piv_chart['refined_usage'],
                    name='World Refined Usage (kt)', marker_color='#ff4757'
                ))
                piv_chart['balance'] = piv_chart['refined_production'] - piv_chart['refined_usage']
                fig_fund.add_trace(go.Scatter(
                    x=piv_chart['period_year'], y=piv_chart['balance'],
                    mode='lines+markers', name='Apparent Surplus / Deficit (kt)',
                    line=dict(color='#fbc531', width=3)
                ))
                fig_fund.update_layout(
                    barmode='group', template='plotly_dark', height=400,
                    margin=dict(l=20, r=20, t=30, b=20),
                    yaxis_title="Thousand Metric Tons (kt)",
                    title="ICSG World Refined Production, Usage and Balance (kt)"
                )
                st.plotly_chart(fig_fund, use_container_width=True)

            st.warning("""
            ⚠️ **Temporal Integrity Disclosure:** Fundamental S&D balances are published with a 60–90 day lag.
            The model strictly forbids interpolating annual figures into past daily prices before their verified release date (`available_at`).
            """)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 6: MULTI-FACTOR RELATIONSHIP LAB
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[5]:
        st.subheader("6. Cross-Variable Relationship Lab")
        st.caption("Interactive bivariate scatter, correlation, and regression between any two series in the Copper Research Foundation.")

        candidate_cols = {
            "Copper Price ($/lb)": "price",
            "Weekly Copper Return (%)": "weekly_price_return",
            "Managed Money Net Position (ctrs)": "primary_spec_net",
            "Managed Money Net % of OI": "managed_money_net_pct_oi",
            "Producer / Merchant Net % of OI": "prod_merc_net_pct_oi",
            "US 10Y Real Yield (%)": "us_10y_real_yield",
            "Nominal Broad USD Index": "nominal_broad_usd_index"
        }

        col_x, col_y, col_lag = st.columns([2, 2, 1])
        with col_x:
            sel_x_label = st.selectbox("Select Independent Variable (X):", list(candidate_cols.keys()), index=3)
        with col_y:
            sel_y_label = st.selectbox("Select Dependent Variable (Y):", list(candidate_cols.keys()), index=1)
        with col_lag:
            sel_lag = st.number_input("Lag (Periods):", min_value=-12, max_value=12, value=0, help="Positive lag: X leads Y.")

        col_x_name = candidate_cols[sel_x_label]
        col_y_name = candidate_cols[sel_y_label]

        sub_rel = aligned_df[[col_x_name, col_y_name]].dropna().copy()
        if sel_lag != 0:
            sub_rel[col_x_name] = sub_rel[col_x_name].shift(sel_lag)
            sub_rel = sub_rel.dropna()

        if len(sub_rel) > 15:
            # Scatter Plot with Trendline
            fig_scat = px.scatter(
                sub_rel, x=col_x_name, y=col_y_name, trendline="ols",
                title=f"{sel_y_label} vs {sel_x_label} (Lag = {sel_lag})",
                template="plotly_dark",
                labels={col_x_name: sel_x_label, col_y_name: sel_y_label}
            )
            fig_scat.update_traces(marker=dict(color='#4bcffa', opacity=0.7, size=6))
            fig_scat.update_layout(height=420, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_scat, use_container_width=True)

            # Correlation metrics
            p_corr = sub_rel[col_x_name].corr(sub_rel[col_y_name], method='pearson')
            s_corr = sub_rel[col_x_name].corr(sub_rel[col_y_name], method='spearman')

            cr1, cr2, cr3 = st.columns(3)
            with cr1:
                st.metric("Pearson Correlation (Linear)", f"{p_corr:+.3f}")
            with cr2:
                st.metric("Spearman Rank Correlation (Monotonic)", f"{s_corr:+.3f}")
            with cr3:
                st.metric("Sample Size (N)", f"{len(sub_rel)} periods")
        else:
            st.info("Insufficient overlapping observations for selected variables.")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 7: RESEARCH BRIEFING
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[6]:
        st.subheader("7. Copper Quantitative Research Briefing")
        st.caption("Institutional research synthesis for the current market state.")

        st.markdown(f"""
        ### Executive Synthesis for Copper (`HG=F` / `085692`)
        - **Current Price:** `${c_p:.4f}/lb` (Weekly change: `{p_delta_pct:+.2f}%`).
        - **Speculative Bias:** Managed Money holds a net position of `{mm_net:+,.0f} contracts` (`{mm_net_pct:+.1f}% of Open Interest`).
        - **Commercial Offset:** Producers maintain `{prod_net:+,.0f} contracts` in net hedging (`{prod_net_pct:+.1f}% of OI`).
        - **Macro Environment:** US 10-Year Real Yield stands at `{ry:.2f}%`, while the Broad Dollar Index is `{dxy:.2f}`.
        - **Physical Balance:** ICSG apparent refined market balance records `{bal_kt:+,.0f} kt`.
        """)

