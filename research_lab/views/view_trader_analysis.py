"""
COT DATA RESEARCH LAB — Module 3: Trader Behavior & Composition Analysis
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from research_lab.config import COLORS
from research_lab.metrics_engine import (
    compute_trader_metrics,
    compute_positioning_divergence,
    compute_rolling_pair_correlation,
    align_price_with_cot
)

def render_trader_analysis(market_df, report_family_name, commodity_label, price_df=None):
    st.title(f"👥 Trader Behavior & Positioning Breakdown — {commodity_label}")
    st.caption(f"Category decomposition under {report_family_name} reporting standards.")

    if market_df.empty:
        st.warning("No data available for the selected market.")
        return

    m_df = compute_trader_metrics(market_df, report_family_name)

    tabs = st.tabs(["👤 Individual Trader Deep-Dive", "⚖️ Cross-Category Comparison", "🏢 Concentration & Market Structure"])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1: INDIVIDUAL TRADER DEEP DIVE
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[0]:
        if "Disaggregated" in report_family_name:
            cat_options = {
                "Managed Money (Speculators)": {
                    "prefix": "M_Money", "net_col": "managed_money_net", "pct_col": "managed_money_net_pct_oi",
                    "spread_col": "M_Money_Positions_Spread_All", "trader_cnt_col": "Traders_M_Money_Long_All",
                    "color": COLORS["managed_money"]
                },
                "Producer / Merchant / Processor": {
                    "prefix": "Prod_Merc", "net_col": "prod_merc_net", "pct_col": "prod_merc_net_pct_oi",
                    "spread_col": None, "trader_cnt_col": "Traders_Prod_Merc_Long_All",
                    "color": COLORS["prod_merc"]
                },
                "Swap Dealers": {
                    "prefix": "Swap", "net_col": "swap_net", "pct_col": "swap_net_pct_oi",
                    "spread_col": "Swap__Positions_Spread_All", "trader_cnt_col": "Traders_Swap_Long_All",
                    "color": COLORS["swap_dealer"]
                },
                "Other Reportables": {
                    "prefix": "Other_Rept", "net_col": "other_rept_net", "pct_col": "other_rept_net_pct_oi",
                    "spread_col": "Other_Rept_Positions_Spread_All", "trader_cnt_col": "Traders_Other_Rept_Long_All",
                    "color": COLORS["other_rept"]
                },
                "Nonreportable (Small Traders)": {
                    "prefix": "NonRept", "net_col": "non_rept_net", "pct_col": "non_rept_net_pct_oi",
                    "spread_col": None, "trader_cnt_col": None,
                    "color": COLORS["non_rept"]
                }
            }
        else:
            cat_options = {
                "Leveraged Money (Hedge Funds)": {
                    "prefix": "Lev_Money", "net_col": "lev_money_net", "pct_col": "lev_money_net_pct_oi",
                    "spread_col": "Lev_Money_Positions_Spread_All", "trader_cnt_col": "Traders_Lev_Money_Long_All",
                    "color": COLORS["lev_money"]
                },
                "Asset Manager / Institutional": {
                    "prefix": "Asset_Mgr", "net_col": "asset_mgr_net", "pct_col": "asset_mgr_net_pct_oi",
                    "spread_col": "Asset_Mgr_Positions_Spread_All", "trader_cnt_col": "Traders_Asset_Mgr_Long_All",
                    "color": COLORS["asset_mgr"]
                },
                "Dealer / Intermediary": {
                    "prefix": "Dealer", "net_col": "dealer_net", "pct_col": "dealer_net_pct_oi",
                    "spread_col": "Dealer_Positions_Spread_All", "trader_cnt_col": "Traders_Dealer_Long_All",
                    "color": COLORS["dealer"]
                },
                "Other Reportables": {
                    "prefix": "Other_Rept", "net_col": "other_rept_net", "pct_col": "other_rept_net_pct_oi",
                    "spread_col": "Other_Rept_Positions_Spread_All", "trader_cnt_col": "Traders_Other_Rept_Long_All",
                    "color": COLORS["tff_other"]
                }
            }

        sel_cat_name = st.selectbox("Select Trader Category to Inspect:", list(cat_options.keys()))
        meta = cat_options[sel_cat_name]
        p = meta["prefix"]

        long_col = f"{p}_Positions_Long_All"
        short_col = f"{p}_Positions_Short_All" if f"{p}_Positions_Short_All" in m_df.columns else f"{p}__Positions_Short_All"
        net_col = meta["net_col"]

        # Latest values
        latest = m_df.iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric(
                "Gross Longs", f"{latest[long_col]:,.0f} ctrs",
                help="- **Formula:** Sum of all open long futures contracts held by this cohort.\n\n- **Purpose:** Measures aggregate bullish commitment and upside positioning capacity."
            )
        with c2:
            st.metric(
                "Gross Shorts", f"{latest[short_col]:,.0f} ctrs",
                help="- **Formula:** Sum of all open short futures contracts held by this cohort.\n\n- **Purpose:** Measures aggregate hedging intensity or downside speculative interest."
            )
        with c3:
            st.metric(
                "Net Position", f"{latest[net_col]:+,.0f} ctrs", delta=f"{latest[meta['pct_col']]:.1f}% of OI",
                help="- **Formula:** Net = Gross Longs - Gross Shorts\n\n- **Purpose:** Quantifies net directional bias (Positive = Net Long, Negative = Net Short). Delta reflects position normalized as % of total Open Interest."
            )
        with c4:
            ls_ratio = (latest[long_col] / latest[short_col]) if latest[short_col] > 0 else 0
            st.metric(
                "Long / Short Ratio", f"{ls_ratio:.2f}x",
                help="- **Formula:** Long / Short Ratio = Gross Longs / Gross Shorts\n\n- **Purpose:** Measures positioning imbalance. Ratios > 2.0x-3.0x signal crowded long positioning and liquidation vulnerability."
            )

        # 1. Long vs Short and Net Charts
        st.subheader("1. Gross Positions (Long vs Short) & Net Exposure")

        has_p_data = False
        p_df = pd.DataFrame()
        if commodity_label in ["Copper", "Silver", "Platinum"] and price_df is not None:
            p_df = align_price_with_cot(m_df, price_df, commodity_label)
            if not p_df.empty and 'price' in p_df.columns:
                has_p_data = True

        c_sw1, c_sw2 = st.columns([3, 1])
        with c_sw2:
            show_trader_price = st.checkbox("Overlay Price on Net", value=False, disabled=not has_p_data)

        if show_trader_price and has_p_data:
            fig_ls = make_subplots(
                rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                row_heights=[0.55, 0.45],
                specs=[[{"secondary_y": False}], [{"secondary_y": True}]]
            )
        else:
            fig_ls = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.6, 0.4])
        
        # Long and Short Lines
        fig_ls.add_trace(go.Scatter(
            x=m_df['report_date'], y=m_df[long_col], mode='lines', name='Gross Long',
            line=dict(color=COLORS['long'], width=2)
        ), row=1, col=1)
        fig_ls.add_trace(go.Scatter(
            x=m_df['report_date'], y=m_df[short_col], mode='lines', name='Gross Short',
            line=dict(color=COLORS['short'], width=2)
        ), row=1, col=1)

        # Net Position Bar / Line
        fig_ls.add_trace(go.Scatter(
            x=m_df['report_date'], y=m_df[net_col], mode='lines', name='Net Position',
            line=dict(color=meta['color'], width=2.5),
            fill='tozeroy', fillcolor=f"rgba(136, 84, 208, 0.15)"
        ), row=2, col=1, secondary_y=False if (show_trader_price and has_p_data) else None)
        fig_ls.add_hline(y=0, line_dash='dash', line_color='gray', row=2, col=1)

        if show_trader_price and has_p_data:
            fig_ls.add_trace(go.Scatter(
                x=p_df['report_date'], y=p_df['price'], mode='lines',
                name=f'{commodity_label} Price ($)',
                line=dict(color='#fbc531', width=2)
            ), row=2, col=1, secondary_y=True)
            fig_ls.update_yaxes(title_text="Settlement Price ($)", row=2, col=1, secondary_y=True, showgrid=False)
            fig_ls.update_yaxes(title_text="Net Contracts", row=2, col=1, secondary_y=False)
        else:
            fig_ls.update_yaxes(title_text="Net Contracts", row=2, col=1)

        fig_ls.update_yaxes(title_text="Gross Contracts", row=1, col=1)

        fig_ls.update_layout(
            template='plotly_dark', height=460,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation='h', y=1.05, x=0)
        )
        st.plotly_chart(fig_ls, use_container_width=True)

        # 2. Trader Counts and Concentration
        if meta["trader_cnt_col"] and meta["trader_cnt_col"] in m_df.columns:
            st.subheader("2. Breadth of Participation: Active Reporting Trader Counts")
            fig_tc = go.Figure()
            fig_tc.add_trace(go.Bar(
                x=m_df['report_date'], y=m_df[meta["trader_cnt_col"]],
                marker_color=meta['color'], opacity=0.7, name='Reporting Trader Count'
            ))
            fig_tc.update_layout(
                template='plotly_dark', height=240,
                margin=dict(l=20, r=20, t=20, b=20),
                yaxis_title="Number of Filing Entities"
            )
            st.plotly_chart(fig_tc, use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2: MULTI-TRADER COMPARISON
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[1]:
        st.subheader("Cross-Category Net Positioning Comparison (% of Open Interest)")
        st.caption("Standardized to percentage of Open Interest to ensure meaningful cross-category scale parity.")

        # --- A. Physical Settlement Price Overlay Check ---
        has_price_data = False
        price_aligned_df = pd.DataFrame()
        if price_df is not None and not price_df.empty:
            price_aligned_df = align_price_with_cot(m_df, price_df, commodity_label)
            if not price_aligned_df.empty and 'price' in price_aligned_df.columns:
                has_price_data = True

        c_opt1, c_opt2 = st.columns([1, 2])
        with c_opt1:
            show_price = st.checkbox(
                "📈 Overlay Settlement Price",
                value=has_price_data,
                disabled=not has_price_data,
                help="Overlay verified physical settlement price for Copper, Silver, or Platinum."
            )
            if not has_price_data:
                st.caption("*(Price overlay available for Copper, Silver, Platinum)*")
        with c_opt2:
            if show_price and has_price_data:
                price_norm_choice = st.radio(
                    "Price Normalization:",
                    ["Raw Settlement Price ($)", "Normalized Scale (0 - 100%)", "Z-Score Standardized (σ)", "Rebased Index (Base = 100)"],
                    horizontal=True
                )
            else:
                price_norm_choice = None

        # Build Main Positioning (+ optional Price) Chart
        if show_price and has_price_data:
            fig_comp = make_subplots(specs=[[{"secondary_y": True}]])
        else:
            fig_comp = go.Figure()

        # Add Trader Traces
        if "Disaggregated" in report_family_name:
            trader_traces = [
                ('managed_money_net_pct_oi', 'Managed Money (% OI)', COLORS['managed_money'], 2.0, None),
                ('prod_merc_net_pct_oi', 'Producer / Merchant (% OI)', COLORS['prod_merc'], 2.0, None),
                ('swap_net_pct_oi', 'Swap Dealers (% OI)', COLORS['swap_dealer'], 1.5, 'dot'),
                ('other_rept_net_pct_oi', 'Other Reportables (% OI)', COLORS['other_rept'], 1.5, None)
            ]
        else:
            trader_traces = [
                ('lev_money_net_pct_oi', 'Leveraged Money (% OI)', COLORS['lev_money'], 2.0, None),
                ('asset_mgr_net_pct_oi', 'Asset Manager (% OI)', COLORS['asset_mgr'], 2.0, None),
                ('dealer_net_pct_oi', 'Dealer / Intermediary (% OI)', COLORS['dealer'], 1.5, None)
            ]

        for col_name, trace_label, trace_color, line_w, dash_style in trader_traces:
            trace_kw = dict(
                x=m_df['report_date'], y=m_df[col_name],
                mode='lines', name=trace_label,
                line=dict(color=trace_color, width=line_w, dash=dash_style)
            )
            if show_price and has_price_data:
                fig_comp.add_trace(go.Scatter(**trace_kw), secondary_y=False)
            else:
                fig_comp.add_trace(go.Scatter(**trace_kw))

        # Add Physical Price Trace if enabled
        if show_price and has_price_data:
            if price_norm_choice == "Raw Settlement Price ($)":
                py_series = price_aligned_df['price']
                py_title = f"{commodity_label} Price ($)"
                p_label = f"{commodity_label} Settlement ($)"
            elif price_norm_choice == "Normalized Scale (0 - 100%)":
                py_series = price_aligned_df['price_norm_pct']
                py_title = "Price Index (0 - 100%)"
                p_label = f"{commodity_label} Price (0-100%)"
            elif price_norm_choice == "Z-Score Standardized (σ)":
                py_series = price_aligned_df['price_zscore']
                py_title = "Price Z-Score (σ)"
                p_label = f"{commodity_label} Price Z-Score"
            else:
                py_series = price_aligned_df['price_rebased']
                py_title = "Rebased Price (Base = 100)"
                p_label = f"{commodity_label} Price (100=Start)"

            fig_comp.add_trace(
                go.Scatter(
                    x=price_aligned_df['report_date'],
                    y=py_series,
                    mode='lines',
                    name=p_label,
                    line=dict(color='#fbc531', width=2.5)
                ),
                secondary_y=True
            )
            fig_comp.update_yaxes(title_text=py_title, secondary_y=True, showgrid=False)
            fig_comp.update_yaxes(title_text="Net Position (% of Total OI)", secondary_y=False)
        else:
            fig_comp.update_layout(yaxis_title="Net Position (% of Total OI)")

        fig_comp.add_hline(y=0, line_dash='dash', line_color='gray')
        fig_comp.update_layout(
            template='plotly_dark', height=420,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation='h', y=1.06, x=0)
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        # ─────────────────────────────────────────────────────────────────────
        # 1. POSITIONING DIVERGENCE PANEL
        # ─────────────────────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("⚡ Positioning Divergence: Speculative vs Commercial Wedge")
        st.caption("Quantifies the structural distance between speculative trend positioning and commercial operational hedging.")

        div_df = compute_positioning_divergence(m_df, report_family_name)
        if 'divergence_spread' in div_df.columns and not div_df['divergence_spread'].isna().all():
            latest_div = div_df.iloc[-1]
            curr_spread = latest_div['divergence_spread']
            z52 = latest_div.get('divergence_zscore_52w', 0.0)
            z156 = latest_div.get('divergence_zscore_156w', 0.0)

            # Imbalance Regime Diagnosis
            if z52 >= 2.0:
                regime_icon = "🔴"
                regime_name = "Extreme Speculative Wedge (Short Squeeze Risk)"
                regime_desc = "Speculators holding record longs against exhausted commercial producers."
            elif z52 >= 1.0:
                regime_icon = "🟠"
                regime_name = "Elevated Speculative Dominance"
                regime_desc = "Speculative long bias significantly above annual norm."
            elif z52 <= -2.0:
                regime_icon = "🔵"
                regime_name = "Commercial Overhang / Speculative Retreat"
                regime_desc = "Commercials under-hedged or speculators heavily short."
            elif z52 <= -1.0:
                regime_icon = "🟡"
                regime_name = "Subdued Speculative Participation"
                regime_desc = "Speculators positioned below commercial baseline."
            else:
                regime_icon = "🟢"
                regime_name = "Structural Hedging Balance"
                regime_desc = "Normal equilibrium between commercial hedging and speculative liquidity."

            kd1, kd2, kd3, kd4 = st.columns(4)
            with kd1:
                st.metric("Divergence Spread", f"{curr_spread:+.1f}% OI", delta=f"{curr_spread - div_df['divergence_spread'].iloc[-2]:+.1f}% WoW")
            with kd2:
                st.metric("52-Week Z-Score", f"{z52:+.2f} σ")
            with kd3:
                st.metric("3-Year (156W) Z-Score", f"{z156:+.2f} σ")
            with kd4:
                st.metric("Positioning Regime", f"{regime_icon} {regime_name.split('(')[0].strip()}", help=regime_desc)

            # Subplot: Divergence Spread and Z-Scores
            fig_div = make_subplots(
                rows=2, cols=1, shared_xaxes=True,
                vertical_spacing=0.08, row_heights=[0.6, 0.4],
                subplot_titles=[
                    f"Divergence Spread: {div_df['divergence_label'].iloc[-1]}",
                    "Rolling Z-Score of Positioning Wedge (Standard Deviations σ)"
                ]
            )

            # Row 1: Raw Spread
            fig_div.add_trace(go.Scatter(
                x=div_df['report_date'], y=div_df['divergence_spread'],
                mode='lines', name='Divergence Spread (% OI)',
                line=dict(color='#e056fd', width=2),
                fill='tozeroy', fillcolor='rgba(224, 86, 253, 0.12)'
            ), row=1, col=1)
            fig_div.add_hline(y=0, line_dash='dash', line_color='gray', row=1, col=1)

            # Row 2: Rolling Z-Scores with Alert Bands
            if 'divergence_zscore_52w' in div_df.columns:
                fig_div.add_trace(go.Scatter(
                    x=div_df['report_date'], y=div_df['divergence_zscore_52w'],
                    mode='lines', name='52W Rolling Z-Score',
                    line=dict(color='#ff7979', width=2)
                ), row=2, col=1)
            if 'divergence_zscore_156w' in div_df.columns:
                fig_div.add_trace(go.Scatter(
                    x=div_df['report_date'], y=div_df['divergence_zscore_156w'],
                    mode='lines', name='156W (3Y) Rolling Z-Score',
                    line=dict(color='#f6e58d', width=1.5, dash='dot')
                ), row=2, col=1)

            fig_div.add_hline(y=2.0, line_dash='dash', line_color='#eb4d4b', row=2, col=1)
            fig_div.add_hline(y=-2.0, line_dash='dash', line_color='#eb4d4b', row=2, col=1)
            fig_div.add_hline(y=0, line_dash='solid', line_color='gray', row=2, col=1)

            fig_div.update_layout(
                template='plotly_dark', height=460,
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation='h', y=1.05, x=0)
            )
            fig_div.update_yaxes(title_text="% of Total OI", row=1, col=1)
            fig_div.update_yaxes(title_text="Z-Score (σ)", row=2, col=1)
            st.plotly_chart(fig_div, use_container_width=True)

        # ─────────────────────────────────────────────────────────────────────
        # 2. MULTI-HORIZON ROLLING CORRELATION PANEL
        # ─────────────────────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("🔄 Multi-Horizon Rolling Correlation Panel (13W, 26W, 52W)")
        st.caption("Inspects structural co-movement and regime breakdown between trader cohorts across varying memory windows.")

        # Correlation Pair Options based on active report family
        if "Disaggregated" in report_family_name:
            pair_options = {
                "Managed Money vs Producer / Merchant (Spec vs Hedger)": ("managed_money_net_pct_oi", "prod_merc_net_pct_oi"),
                "Managed Money vs Swap Dealers": ("managed_money_net_pct_oi", "swap_net_pct_oi"),
                "Producer / Merchant vs Swap Dealers": ("prod_merc_net_pct_oi", "swap_net_pct_oi"),
                "Managed Money vs Other Reportables": ("managed_money_net_pct_oi", "other_rept_net_pct_oi")
            }
        else:
            pair_options = {
                "Leveraged Money vs Dealer / Intermediary": ("lev_money_net_pct_oi", "dealer_net_pct_oi"),
                "Leveraged Money vs Asset Manager": ("lev_money_net_pct_oi", "asset_mgr_net_pct_oi"),
                "Asset Manager vs Dealer / Intermediary": ("asset_mgr_net_pct_oi", "dealer_net_pct_oi")
            }

        col_p1, col_p2 = st.columns([2, 1])
        with col_p1:
            sel_pair_label = st.selectbox("Select Trader Cohorts for Correlation Analysis:", list(pair_options.keys()))
        with col_p2:
            corr_basis = st.radio("Correlation Metric:", ["Position Level (% OI)", "Weekly Flow (Δ Net)"], horizontal=True)

        col_a, col_b = pair_options[sel_pair_label]
        use_changes = (corr_basis == "Weekly Flow (Δ Net)")

        corr_df = compute_rolling_pair_correlation(m_df, col_a, col_b, windows=[13, 26, 52], use_changes=use_changes)

        if not corr_df.empty:
            c_latest = corr_df.iloc[-1]
            c13 = c_latest.get('corr_13w', np.nan)
            c26 = c_latest.get('corr_26w', np.nan)
            c52 = c_latest.get('corr_52w', np.nan)

            kc1, kc2, kc3, kc4 = st.columns(4)
            with kc1:
                st.metric(
                    "13-Week Correlation (Tactical)", f"{c13:+.2f}" if pd.notna(c13) else "N/A",
                    help="- **Formula:** Rolling 13-week Pearson correlation coefficient r between cohort positions.\n\n- **Purpose:** Measures short-term tactical co-movement. Negative values (-0.8 to -1.0) confirm direct liquidity offset."
                )
            with kc2:
                st.metric(
                    "26-Week Correlation (Medium-Term)", f"{c26:+.2f}" if pd.notna(c26) else "N/A",
                    help="- **Formula:** Rolling 26-week (half-year) Pearson correlation coefficient r.\n\n- **Purpose:** Evaluates medium-term structural synchronization or regime shifts."
                )
            with kc3:
                st.metric(
                    "52-Week Correlation (Structural)", f"{c52:+.2f}" if pd.notna(c52) else "N/A",
                    help="- **Formula:** Rolling 52-week (1-year) Pearson correlation coefficient r.\n\n- **Purpose:** Quantifies foundational relationship between speculative liquidity and commercial hedging."
                )
            with kc4:
                if pd.notna(c52):
                    if c52 <= -0.6:
                        rel_eval = "Inverse Hedging (Normal)"
                    elif c52 >= 0.3:
                        rel_eval = "Positive Synchronization (Abnormal)"
                    else:
                        rel_eval = "Decoupled / Transition"
                else:
                    rel_eval = "Insufficient Data"
                st.metric(
                    "Structural State", rel_eval,
                    help="- **Inverse Hedging (r <= -0.6):** Healthy commercial absorption of speculative flows.\n\n- **Positive Synchronization (r >= +0.3):** Anomalous co-trending (both cohorts buying or selling).\n\n- **Decoupled (-0.6 < r < +0.3):** Neutral or transitional liquidity state."
                )

            fig_corr = go.Figure()
            fig_corr.add_trace(go.Scatter(
                x=corr_df['report_date'], y=corr_df['corr_13w'],
                mode='lines', name='13-Week Rolling (Tactical)',
                line=dict(color='#00d2d3', width=1.5, dash='dot')
            ))
            fig_corr.add_trace(go.Scatter(
                x=corr_df['report_date'], y=corr_df['corr_26w'],
                mode='lines', name='26-Week Rolling (Medium)',
                line=dict(color='#48dbfb', width=2, dash='dash')
            ))
            fig_corr.add_trace(go.Scatter(
                x=corr_df['report_date'], y=corr_df['corr_52w'],
                mode='lines', name='52-Week Rolling (Structural 1Y)',
                line=dict(color='#a55eea', width=2.8)
            ))

            fig_corr.add_hline(y=0, line_dash='solid', line_color='gray')
            fig_corr.add_hline(y=-0.7, line_dash='dash', line_color='rgba(46, 204, 113, 0.6)', annotation_text="Strong Negative (-0.7)")
            fig_corr.add_hline(y=0.7, line_dash='dash', line_color='rgba(235, 77, 75, 0.6)', annotation_text="Strong Positive (+0.7)")

            fig_corr.update_layout(
                template='plotly_dark', height=380,
                margin=dict(l=20, r=20, t=30, b=20),
                yaxis=dict(title="Pearson Correlation (r)", range=[-1.05, 1.05]),
                legend=dict(orientation='h', y=1.05, x=0)
            )
            st.plotly_chart(fig_corr, use_container_width=True)

        st.markdown("""
        **Institutional Co-Movement Principles:**
        - **Persistent Negative Correlation (r ≈ -0.80 to -0.95):** Reflects the canonical role of futures markets: commercial producers transfer price risk to speculative money managers who provide liquidity.
        - **Correlation Breakdown (r approaching 0 or positive):** Signals non-standard regime shifts such as market illiquidity, forced deleveraging events, or commercial physical hoarding.
        """)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3: CONCENTRATION ANALYSIS
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[2]:
        st.subheader("Concentration of Open Interest (Top 4 & Top 8 Traders)")
        st.caption("Measures the percentage of gross and net market positions held by the largest market participants.")

        conc_cols = [
            'Conc_Gross_LE_4_TDR_Long_All', 'Conc_Gross_LE_4_TDR_Short_All',
            'Conc_Gross_LE_8_TDR_Long_All', 'Conc_Gross_LE_8_TDR_Short_All'
        ]
        has_conc = all(c in m_df.columns for c in conc_cols)

        if has_conc:
            fig_conc = go.Figure()
            fig_conc.add_trace(go.Scatter(
                x=m_df['report_date'], y=m_df['Conc_Gross_LE_4_TDR_Long_All'],
                mode='lines', name='Top 4 Gross Long Share (%)', line=dict(color=COLORS['long'], width=2)
            ))
            fig_conc.add_trace(go.Scatter(
                x=m_df['report_date'], y=m_df['Conc_Gross_LE_4_TDR_Short_All'],
                mode='lines', name='Top 4 Gross Short Share (%)', line=dict(color=COLORS['short'], width=2)
            ))
            fig_conc.add_trace(go.Scatter(
                x=m_df['report_date'], y=m_df['Conc_Gross_LE_8_TDR_Long_All'],
                mode='lines', name='Top 8 Gross Long Share (%)', line=dict(color=COLORS['long'], width=1.5, dash='dot')
            ))
            fig_conc.add_trace(go.Scatter(
                x=m_df['report_date'], y=m_df['Conc_Gross_LE_8_TDR_Short_All'],
                mode='lines', name='Top 8 Gross Short Share (%)', line=dict(color=COLORS['short'], width=1.5, dash='dot')
            ))
            fig_conc.update_layout(
                template='plotly_dark', height=380,
                margin=dict(l=20, r=20, t=30, b=20),
                yaxis_title="% of Total Gross Open Interest",
                legend=dict(orientation='h', y=1.05, x=0)
            )
            st.plotly_chart(fig_conc, use_container_width=True)

            lat = m_df.iloc[-1]
            st.markdown(f"""
            **Current Concentration Metrics:**
            - **Top 4 Traders Gross Long Share:** `{lat['Conc_Gross_LE_4_TDR_Long_All']:.1f}%`
            - **Top 4 Traders Gross Short Share:** `{lat['Conc_Gross_LE_4_TDR_Short_All']:.1f}%`
            - **Top 8 Traders Gross Long Share:** `{lat['Conc_Gross_LE_8_TDR_Long_All']:.1f}%`
            - **Top 8 Traders Gross Short Share:** `{lat['Conc_Gross_LE_8_TDR_Short_All']:.1f}%`
            """)
        else:
            st.info("Concentration fields not available for this selected series.")

