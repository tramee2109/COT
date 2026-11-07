"""
COT DATA RESEARCH LAB — Module 6: COT & Price Relationship Lab
Dedicated quantitative workspace testing whether COT positioning contains information about commodity prices.
Strictly analytical & educational research platform (non-trading, no signals, no automated execution).
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from research_lab.config import COLORS
from research_lab.metrics_engine import (
    compute_trader_metrics,
    compute_position_decomposition,
    compute_rolling_momentum,
    compute_historical_extremes
)
from research_lab.price_engine import (
    audit_price_data,
    COT_PRICE_MARKET_REGISTRY,
    align_cot_and_price,
    compute_positioning_price_correlation,
    compute_lead_lag_cross_correlation,
    compute_forward_returns_by_quantile,
    run_extreme_event_study,
    run_flow_event_study,
    run_hac_regression,
    compute_information_coefficients,
    run_multiple_testing_adjustment,
    compute_2d_regime_matrix
)

def render_evaluation(market_df, report_family_name, commodity_label, price_df):
    st.title(f"🧪 COT & Price Relationship Lab — {commodity_label}")
    st.caption("Quantitative workspace investigating empirical positioning-price relationships, lead-lag dynamics, event studies, and statistical significance.")

    st.warning("""
    ⚠️ **Research Governance Notice:**
    This module evaluates empirical statistical associations, information content, and regime behavior.
    **It is strictly NOT a trading strategy, buy/sell signal generator, or automated execution system.**
    """)

    if market_df.empty:
        st.warning("No data available for the selected market.")
        return

    # Check commodity price availability
    if commodity_label not in ["Copper", "Silver", "Platinum"]:
        st.info(f"""
        **Missing Verified Physical Price Data for '{commodity_label}':**
        Verified continuous daily settlement prices are currently curated for **Copper**, **Silver**, and **Platinum**.
        Selected contract code does not have an active physical futures settlement mapping in the workspace.
        COT positioning metrics remain fully accessible in Modules 1–5.
        """)
        return

    # Base Metrics Ingestion
    m_df = compute_trader_metrics(market_df, report_family_name)
    spec_prefix = "M_Money" if "Disaggregated" in report_family_name else "Lev_Money"
    m_df = compute_position_decomposition(m_df, category_prefix=spec_prefix)
    m_df = compute_rolling_momentum(m_df, series_col="primary_spec_net", windows=[4, 8, 13, 26])
    m_df = compute_historical_extremes(m_df, series_col="primary_spec_net", lookback_window=52)

    # ─────────────────────────────────────────────────────────────────────────
    # 1. RESEARCH QUESTION BUILDER (SECTION 6.1)
    # ─────────────────────────────────────────────────────────────────────────
    with st.expander("🔬 Interactive Research Question & Protocol Builder", expanded=True):
        col_b1, col_b2, col_b3 = st.columns(3)

        with col_b1:
            if "Disaggregated" in report_family_name:
                trader_cat = st.selectbox(
                    "Trader Cohort:",
                    ["Managed Money (Speculators)", "Producer / Merchant (Commercials)", "Swap Dealers", "Other Reportables"]
                )
                var_mapping = {
                    "Managed Money (Speculators)": "managed_money_net_pct_oi",
                    "Producer / Merchant (Commercials)": "prod_merc_net_pct_oi",
                    "Swap Dealers": "swap_net_pct_oi",
                    "Other Reportables": "other_rept_net_pct_oi"
                }
            else:
                trader_cat = st.selectbox(
                    "Trader Cohort:",
                    ["Leveraged Money (Hedge Funds)", "Asset Manager / Institutional", "Dealer / Intermediary"]
                )
                var_mapping = {
                    "Leveraged Money (Hedge Funds)": "lev_money_net_pct_oi",
                    "Asset Manager / Institutional": "asset_mgr_net_pct_oi",
                    "Dealer / Intermediary": "dealer_net_pct_oi"
                }

            sel_base_var = var_mapping[trader_cat]

        with col_b2:
            hypothesis_choice = st.selectbox(
                "Research Hypothesis:",
                [
                    "Contemporaneous Co-Movement (Do positions move with price?)",
                    "Positioning Leads Price (Does COT predict returns?)",
                    "Price Leads Positioning (Do traders chase price trends?)",
                    "Positioning Extremes Reversal (Do |Z| > 2σ forecast turning points?)",
                    "Flow Drivers Information (Does Accumulation outperform Liquidation?)",
                    "Regime-Dependent Behavior (Does positioning impact vary in Bull vs Bear?)"
                ]
            )

        with col_b3:
            price_convention = st.selectbox(
                "Price Alignment Convention:",
                [
                    "Publication-Aware (Friday Close Anchor - Zero Lookahead)",
                    "Tuesday Survey Close (Contemporaneous Benchmark Only)"
                ]
            )
            conv_code = "publication_aware" if "Publication-Aware" in price_convention else "tuesday_close"

    # Align COT and Price with Selected Convention
    aligned_df = align_cot_and_price(m_df, commodity_label, convention=conv_code)
    if aligned_df.empty:
        st.error("Failed to align COT positions with commodity settlement price history.")
        return

    # Protocol Summary Banner
    meta_info = COT_PRICE_MARKET_REGISTRY.get(commodity_label, {})
    st.markdown(f"""
    <div style="background: rgba(44, 62, 80, 0.4); border-left: 3px solid #4bcffa; padding: 10px 14px; border-radius: 4px; font-size: 12px; margin-bottom: 15px;">
        <b>Active Research Specification:</b> <code>{commodity_label}</code> ({meta_info.get('exchange', 'COMEX')} | {meta_info.get('price_unit', 'USD')}) &nbsp;|&nbsp;
        <b>Report Standard:</b> {report_family_name} &nbsp;|&nbsp;
        <b>Target Cohort:</b> {trader_cat} &nbsp;|&nbsp;
        <b>Convention:</b> {price_convention.split('(')[0].strip()} &nbsp;|&nbsp;
        <b>Aligned Obs:</b> {len(aligned_df)} weekly periods ({aligned_df['report_date'].min().strftime('%Y-%m-%d')} to {aligned_df['report_date'].max().strftime('%Y-%m-%d')})
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs([
        "📊 Correlation & Lead-Lag Analysis",
        "📈 Forward Returns & Event Studies",
        "📐 Econometric Regression & IC",
        "🔲 2D Positioning & Price Regime Matrix",
        "📋 Price Data Audit & Methodology"
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1: CORRELATION & LEAD-LAG ANALYSIS
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[0]:
        st.subheader("1. Statistical Correlation (Levels vs Flow Changes)")
        st.caption("Distinguishes spurious trending non-stationary level correlations from weekly flow co-movements.")

        col_c1, col_c2 = st.columns(2)

        # Weekly Flow Change Correlation
        aligned_df['weekly_flow_delta'] = aligned_df[sel_base_var].diff(1)
        summ_delta, roll_delta = compute_positioning_price_correlation(
            aligned_df, pos_col='weekly_flow_delta', price_ret_col='weekly_price_return', windows=[13, 26, 52]
        )

        with col_c1:
            st.markdown("#### Weekly Flow vs Weekly Price Return (Stationary $\\Delta$)")
            if summ_delta:
                st.metric(
                    "Pearson Correlation (Flow vs Return)",
                    f"r = {summ_delta['pearson_r']:+.3f}",
                    delta=f"p = {summ_delta['pearson_p']:.4f} ({'Statistically Significant' if summ_delta['is_significant'] else 'Not Significant'})"
                )
                st.markdown(f"""
                - **Spearman Rank Correlation:** `{summ_delta['spearman_r']:+.3f}` (p = `{summ_delta['spearman_p']:.4f}`)
                - **95% Confidence Interval:** `[{summ_delta['ci_low']:+.3f}, {summ_delta['ci_high']:+.3f}]`
                - **Degrees of Freedom (N - 2):** `{summ_delta['sample_size'] - 2}`
                """)

        # Level Correlation (With Cautionary Warning)
        summ_level, roll_level = compute_positioning_price_correlation(
            aligned_df, pos_col=sel_base_var, price_ret_col='price', windows=[13, 26, 52]
        )
        with col_c2:
            st.markdown("#### Cumulative Level vs Price Level (Non-Stationary)")
            if summ_level:
                st.metric(
                    "Pearson Correlation (Level vs Price)",
                    f"r = {summ_level['pearson_r']:+.3f}",
                    delta="Trending Co-Movement (Prone to Spurious Drift)",
                    delta_color="off"
                )
                st.markdown(f"""
                - **Spearman Rank Correlation:** `{summ_level['spearman_r']:+.3f}` (p = `{summ_level['spearman_p']:.4f}`)
                - **Methodological Caution:** Level correlation between trending commodity prices and cumulative positions frequently exhibits common-trend bias.
                """)

        # Rolling Correlation Chart
        st.markdown("---")
        st.subheader("Rolling Multi-Horizon Correlation (Flow Δ vs Price Return)")
        if not roll_delta.empty:
            fig_rc = go.Figure()
            fig_rc.add_trace(go.Scatter(x=roll_delta['report_date'], y=roll_delta['corr_13w'], mode='lines', name='13W Rolling (Quarterly)', line=dict(color='#00d2d3', width=1.5, dash='dot')))
            fig_rc.add_trace(go.Scatter(x=roll_delta['report_date'], y=roll_delta['corr_26w'], mode='lines', name='26W Rolling (Semi-Annual)', line=dict(color='#48dbfb', width=2, dash='dash')))
            fig_rc.add_trace(go.Scatter(x=roll_delta['report_date'], y=roll_delta['corr_52w'], mode='lines', name='52W Rolling (1-Year Core)', line=dict(color='#a55eea', width=2.8)))
            fig_rc.add_hline(y=0, line_dash='solid', line_color='gray')
            fig_rc.update_layout(template='plotly_dark', height=360, margin=dict(l=20, r=20, t=30, b=20), yaxis=dict(title="Pearson Correlation (r)", range=[-1.05, 1.05]), legend=dict(orientation='h', y=1.06, x=0))
            st.plotly_chart(fig_rc, use_container_width=True)

        # Lead-Lag Cross Correlation Analysis
        st.markdown("---")
        st.subheader("2. Lead-Lag Profile: Does Positioning Precede or Follow Price?")
        st.caption("Cross-correlation profile Corr(ΔCOT_t, Return_{t+k}) across ±8 weekly shifts with 95% Bartlett confidence bands.")

        ll_df = compute_lead_lag_cross_correlation(aligned_df, pos_change_col='weekly_flow_delta', price_ret_col='weekly_price_return', max_lag=8)
        if not ll_df.empty:
            fig_ll = go.Figure()
            bar_colors = [
                '#e74c3c' if r['regime'] == 'Price Leads COT (Lag)' else ('#2ecc71' if r['regime'] == 'COT Leads Price (Lead)' else '#f1c40f')
                for _, r in ll_df.iterrows()
            ]
            fig_ll.add_trace(go.Bar(
                x=ll_df['horizon_label'], y=ll_df['spearman_r'],
                marker_color=bar_colors, name='Cross Correlation (Spearman r)'
            ))
            # 95% Bartlett confidence bounds
            fig_ll.add_trace(go.Scatter(x=ll_df['horizon_label'], y=ll_df['ci_95_band'], mode='lines', name='+95% Confidence Band', line=dict(color='rgba(255, 255, 255, 0.4)', dash='dash')))
            fig_ll.add_trace(go.Scatter(x=ll_df['horizon_label'], y=-ll_df['ci_95_band'], mode='lines', name='-95% Confidence Band', line=dict(color='rgba(255, 255, 255, 0.4)', dash='dash')))
            fig_ll.add_hline(y=0, line_dash='solid', line_color='gray')
            fig_ll.update_layout(
                template='plotly_dark', height=380,
                margin=dict(l=20, r=20, t=30, b=20),
                yaxis=dict(title="Spearman Cross-Correlation (r)", range=[-0.45, 0.45]),
                legend=dict(orientation='h', y=1.06, x=0)
            )
            st.plotly_chart(fig_ll, use_container_width=True)

            st.markdown("""
            **Empirical Lead-Lag Diagnostic:**
            - **Left Side ($t-k$W - Red):** Price leads COT. High correlation here proves that traders are **trend-followers** (reallocating capital *after* price has already moved).
            - **Center ($t$ - Gold):** Contemporaneous synchronization during the observation week.
            - **Right Side ($t+k$W - Green):** COT leads price. Statistically significant bars exceeding the dashed band indicate **predictive information content** over future returns.
            """)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2: FORWARD RETURNS & EVENT STUDIES
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[1]:
        st.subheader("1. Forward Return Profiles Across Positioning Quintiles")
        st.caption("Evaluates forward price returns conditioned on sorting the market into 5 positioning quintiles (Q1=Most Bearish/Short to Q5=Most Bullish/Long).")

        col_q1, col_q2 = st.columns([3, 1])
        with col_q2:
            non_overlap = st.checkbox("Non-Overlapping Sampling", value=False, help="Sub-samples every 4 weeks to avoid overlapping multi-week forward return serial dependence.")

        q_df = compute_forward_returns_by_quantile(aligned_df, pos_col=sel_base_var, horizons=[1, 2, 4, 8, 13, 26], q=5, non_overlapping=non_overlap)
        if not q_df.empty:
            st.dataframe(
                q_df.style.format({
                    "Mean_Return_Pct": "{:+.2f}%", "Median_Return_Pct": "{:+.2f}%",
                    "Std_Dev_Pct": "{:.2f}%", "Win_Rate_Pct": "{:.1f}%",
                    "T_Statistic": "{:.2f}", "P_Value": "{:.4f}"
                }),
                use_container_width=True
            )

            # Bar comparison of 4W Forward Return across Quintiles
            q4 = q_df[q_df['Horizon'] == '4W']
            if not q4.empty:
                fig_q = go.Figure()
                fig_q.add_trace(go.Bar(
                    x=q4['Quantile'], y=q4['Mean_Return_Pct'],
                    marker_color=np.where(q4['Mean_Return_Pct'] >= 0, COLORS['long'], COLORS['short']),
                    name='4W Mean Return (%)'
                ))
                fig_q.update_layout(template='plotly_dark', height=280, margin=dict(l=20, r=20, t=30, b=20), yaxis_title="Mean 4-Week Forward Return (%)", title="4-Week Forward Return by Positioning Quintile")
                st.plotly_chart(fig_q, use_container_width=True)

        st.markdown("---")
        st.subheader("2. Positioning Extreme Event Study (|Z| >= 2.0σ)")
        st.caption("Measures subsequent price path after extreme speculative positioning, with optional first-crossing deduplication to avoid event clustering.")

        col_e1, col_e2 = st.columns([3, 1])
        with col_e2:
            dedup = st.checkbox("Deduplicate Event Clusters", value=True, help="Triggers an event ONLY on the first week entering the extreme zone (first-crossing), preventing consecutive weeks from double-counting the same episode.")

        ev_summary, ev_markers, n_hi, n_lo = run_extreme_event_study(aligned_df, z_col='zscore_52w', z_threshold=2.0, deduplicate_clustering=dedup)

        ce1, ce2, ce3 = st.columns(3)
        with ce1:
            st.metric("Extreme Long Episodes (Z >= +2σ)", f"{n_hi} events")
        with ce2:
            st.metric("Extreme Short Episodes (Z <= -2σ)", f"{n_lo} events")
        with ce3:
            st.metric("Event Deduplication Status", "First-Crossing Active" if dedup else "All Consecutive Weeks")

        if not ev_summary.empty:
            st.dataframe(
                ev_summary.style.format({
                    "Mean_Return_Pct": "{:+.2f}%", "Median_Return_Pct": "{:+.2f}%",
                    "Std_Dev_Pct": "{:.2f}%", "Win_Rate_Pct": "{:.1f}%",
                    "T_Stat": "{:.2f}", "P_Value": "{:.4f}"
                }),
                use_container_width=True
            )

            # Cumulative Trajectory Path
            fig_traj = go.Figure()
            for ev_type, color in [("Extreme Long (Z >= +2.0 Std)", '#eb4d4b'), ("Extreme Short (Z <= -2.0 Std)", '#2ecc71'), ("Baseline / Neutral Regime", '#74b9ff')]:
                sub_traj = ev_summary[ev_summary['Event_Type'] == ev_type]
                if not sub_traj.empty:
                    fig_traj.add_trace(go.Scatter(
                        x=sub_traj['Horizon_Label'], y=sub_traj['Mean_Return_Pct'],
                        mode='lines+markers', name=ev_type, line=dict(color=color, width=2.5)
                    ))
            fig_traj.add_hline(y=0, line_dash='dash', line_color='gray')
            fig_traj.update_layout(
                template='plotly_dark', height=360,
                margin=dict(l=20, r=20, t=30, b=20),
                yaxis_title="Mean Cumulative Forward Return (%)",
                title="Forward Cumulative Return Trajectory Following Positioning Regimes"
            )
            st.plotly_chart(fig_traj, use_container_width=True)

        st.markdown("---")
        st.subheader("3. Inferred Flow Driver Event Study")
        st.caption("Compares future commodity price returns following the 4 weekly flow archetypes.")

        flow_ev_df = run_flow_event_study(aligned_df, horizons=[1, 2, 4, 8, 13])
        if not flow_ev_df.empty:
            st.dataframe(
                flow_ev_df.style.format({
                    "Mean_Return_Pct": "{:+.2f}%", "Median_Return_Pct": "{:+.2f}%",
                    "Positive_Return_Rate": "{:.1f}%", "T_Stat": "{:.2f}", "P_Value": "{:.4f}"
                }),
                use_container_width=True
            )

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3: ECONOMETRIC REGRESSION & INFORMATION COEFFICIENT
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[2]:
        st.subheader("1. Econometric Regression (OLS with Newey-West HAC Errors)")
        st.caption("Models forward returns as a function of positioning: Return_{t+h} = α + β·X_t + ε_t with heteroskedasticity and autocorrelation robust standard errors.")

        col_r1, col_r2 = st.columns([2, 1])
        with col_r1:
            sel_target_h = st.selectbox("Select Forward Return Horizon (Dependent Variable Y):", [1, 2, 4, 8, 13, 26], format_func=lambda x: f"{x}-Week Forward Return (fwd_ret_{x}w)")
        with col_r2:
            max_hac_lags = st.slider("Newey-West Max Lag Parameter:", min_value=1, max_value=12, value=sel_target_h)

        reg_res = run_hac_regression(aligned_df, x_col=sel_base_var, y_col=f'fwd_ret_{sel_target_h}w', max_lag=max_hac_lags)
        if reg_res and "error" not in reg_res:
            kr1, kr2, kr3, kr4 = st.columns(4)
            with kr1:
                st.metric(
                    "Slope Coefficient (β)", f"{reg_res['beta']:+.4f}",
                    help="• Formula: OLS slope parameter β from:\n  Return_{t+h} = α + β·Position_t + ε_t\n• Purpose: Measures directional sensitivity of forward returns to positioning. β > 0 indicates trend continuation; β < 0 signals mean reversion."
                )
            with kr2:
                st.metric(
                    "t-statistic (HAC)", f"{reg_res['t_statistic']:.2f}",
                    help="• Formula: t = β / SE_HAC(β), computed using Newey-West spectral variance matrix.\n• Purpose: Tests parameter significance robust to serial autocorrelation (overlapping forward return horizons) and heteroskedasticity. |t| > 1.96 confirms significance at 95% confidence level."
                )
            with kr3:
                st.metric(
                    "p-value", f"{reg_res['p_value']:.4f}", delta="Statistically Significant" if reg_res['is_significant'] else "Not Significant",
                    help="• Formula: Two-tailed Student's t distribution p-value under null hypothesis H0: β = 0.\n• Purpose: If p < 0.05, confirms that the empirical relationship between COT and forward commodity returns is statistically non-random."
                )
            with kr4:
                st.metric(
                    "R-Squared (R²)", f"{reg_res['r_squared'] * 100.0:.2f}%",
                    help="• Formula: R² = 1 - (SS_res / SS_tot)\n• Purpose: Quantifies percentage of forward price return variation explained by positioning. In institutional commodity forecasting, R² between 1% and 5% represents meaningful information content."
                )

            st.markdown(f"""
            - **Intercept (α):** `{reg_res['alpha']:+.3f}%`
            - **HAC Standard Error (SE_β):** `{reg_res['se_beta']:.4f}`
            - **95% Confidence Interval for β:** `[{reg_res['ci_lower']:+.4f}, {reg_res['ci_upper']:+.4f}]`
            - **Sample Size (N):** `{reg_res['n_obs']} observations`
            """)
        elif reg_res and "error" in reg_res:
            st.error(f"Regression calculation error: {reg_res['error']}")

        st.markdown("---")
        st.subheader("2. Multi-Horizon Information Coefficient (IC) & Information Ratio (IR)")
        st.caption("Spearman Rank IC measures monotonic forecasting power. Information Ratio (IR = Mean IC / Std IC) evaluates consistency across time.")

        ic_table, rolling_ic = compute_information_coefficients(aligned_df, pos_col=sel_base_var, horizons=[1, 2, 4, 8, 13, 26])
        if not ic_table.empty:
            # Multiple testing correction
            p_vals = ic_table['Spearman_P_Value'].tolist()
            rej_bh, p_bh = run_multiple_testing_adjustment(p_vals, method='fdr_bh')
            ic_table['FDR_Adjusted_P_Val'] = p_bh
            ic_table['FDR_Significant'] = ["Significant (FDR < 0.05)" if r else "Not Significant" for r in rej_bh]

            st.dataframe(
                ic_table.style.format({
                    "Spearman_Rank_IC": "{:+.4f}", "Spearman_P_Value": "{:.4f}",
                    "Pearson_IC": "{:+.4f}", "Pearson_P_Value": "{:.4f}",
                    "Rolling_IC_Mean": "{:+.4f}", "Rolling_IC_Std": "{:.4f}",
                    "Information_Ratio_IR": "{:+.2f}", "FDR_Adjusted_P_Val": "{:.4f}"
                }),
                use_container_width=True
            )

            # Rolling IC Plot
            fig_ic_roll = go.Figure()
            for h in [1, 4, 13, 26]:
                col_name = f'ic_52w_{h}w'
                if col_name in rolling_ic.columns:
                    fig_ic_roll.add_trace(go.Scatter(
                        x=rolling_ic['report_date'], y=rolling_ic[col_name],
                        mode='lines', name=f'52W Rolling IC ({h}W Forward Return)'
                    ))
            fig_ic_roll.add_hline(y=0, line_dash='dash', line_color='gray')
            fig_ic_roll.update_layout(
                template='plotly_dark', height=360,
                margin=dict(l=20, r=20, t=30, b=20),
                yaxis=dict(title="Rolling Spearman Rank IC", range=[-0.6, 0.6]),
                legend=dict(orientation='h', y=1.06, x=0)
            )
            st.plotly_chart(fig_ic_roll, use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 4: 2D REGIME MATRIX (SECTION 8)
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[3]:
        st.subheader("2D Positioning & Price Regime Matrix")
        st.caption("Cross-tabulates extreme and neutral positioning conditions against market price trend regimes (Uptrend vs Downtrend relative to 50W MA).")

        col_rm1, col_rm2 = st.columns([2, 1])
        with col_rm1:
            mat_horizon = st.radio("Forward Horizon for Regime Matrix:", [1, 4, 13, 26], format_func=lambda x: f"{x}-Week Forward Return", horizontal=True)

        regime_mat = compute_2d_regime_matrix(aligned_df, pos_z_col='zscore_52w', horizon=mat_horizon)
        if not regime_mat.empty:
            st.dataframe(
                regime_mat.style.format({
                    f"Mean_Forward_{mat_horizon}W_Ret_Pct": "{:+.2f}%",
                    f"Median_Forward_{mat_horizon}W_Ret_Pct": "{:+.2f}%",
                    "Win_Rate_Pct": "{:.1f}%",
                    "Realized_Vol_Pct": "{:.2f}%"
                }),
                use_container_width=True
            )

            st.markdown("""
            **Regime Analysis Insight:**
            - **Trend-Aligned Extremes:** When Extreme Speculative Long positioning occurs during an **Uptrend**, the market frequently demonstrates trend continuation rather than mean reversion.
            - **Trend-Counter Extremes:** When Extreme Speculative Long positioning occurs during an established **Downtrend**, it historically signals fragile capitulation and elevated vulnerability to rapid long liquidation.
            """)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 5: PRICE DATA AUDIT & METHODOLOGY
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[4]:
        st.subheader("Price Data Audit & Governance Documentation")
        st.caption("Complete inventory of audited price datasets, continuous roll specifications, and lookahead safeguards.")

        audit_res = audit_price_data()
        st.markdown(f"**Audit Status:** `{audit_res['status']}` | **Curated Commodities:** `{', '.join(audit_res['verified_commodities'])}`")

        st.markdown("#### Audited Local Price Repositories")
        for key, info in audit_res["datasets"].items():
            st.markdown(f"""
            - **{key}:** File `{info['file']}` | Obs: `{info['observations']:,}` | Range: `{info['date_min']} to {info['date_max']}` | Freq: `{info['frequency']}` | Instrument: `{info.get('instrument', 'Continuous Futures')}`
            """)

        st.markdown("---")
        st.markdown("#### Canonical COT-to-Price Mapping Registry")
        reg_records = []
        for comm, meta in COT_PRICE_MARKET_REGISTRY.items():
            reg_records.append({
                "Commodity": comm,
                "CFTC Code": meta['cftc_code'],
                "Exchange": meta['exchange'],
                "Instrument": meta['instrument'],
                "Price Unit": meta['price_unit'],
                "Multiplier": f"{meta['contract_multiplier']:,}",
                "Roll Methodology": meta['roll_methodology'],
                "Status": meta['status']
            })
        st.dataframe(pd.DataFrame(reg_records), use_container_width=True)

        st.markdown(r"""
        #### Critical Lookahead Protection Rules:
        1. **Tuesday Survey vs Friday Release:** CFTC Commitments of Traders positions are measured as of Tuesday close. Official release occurs Friday at 3:30 PM Eastern Time.
        2. **Forward Return Anchor:** In `Publication-Aware` mode, forward returns ($h$ weeks) are anchored strictly on **Friday's closing price**, completely preventing information leakage from Tuesday through Friday.
        3. **Stationarity Principle:** All econometric regressions and event studies evaluate percentage returns and weekly flow changes ($\Delta$), avoiding spurious correlations associated with trending non-stationary level series.
        """)
