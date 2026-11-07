"""
COT DATA RESEARCH LAB — Module 4: Positioning Dynamics & Flow Decomposition
Integrated with Commodity Price Behavior (Phase 11)
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from research_lab.config import COLORS, DEFAULT_LOOKBACK_WEEKS, LOOKBACK_OPTIONS
from research_lab.metrics_engine import (
    compute_trader_metrics,
    compute_position_decomposition,
    compute_rolling_momentum,
    compute_historical_extremes
)
from research_lab.price_engine import align_cot_and_price

def render_positioning_dynamics(market_df, report_family_name, commodity_label, price_df=None):
    st.title(f"⚡ Positioning Dynamics & Flow Decomposition — {commodity_label}")
    st.caption("Investigate weekly positioning velocities, flow composition, acceleration, and historical extremes connected with price behavior.")

    if market_df.empty:
        st.warning("No data available for the selected market.")
        return

    m_df = compute_trader_metrics(market_df, report_family_name)
    spec_prefix = "M_Money" if "Disaggregated" in report_family_name else "Lev_Money"

    # Compute decomposition & rolling dynamics
    m_df = compute_position_decomposition(m_df, category_prefix=spec_prefix)
    m_df = compute_rolling_momentum(m_df, series_col="primary_spec_net", windows=[4, 8, 13, 26])

    # Lookback window selector
    col_ctrl1, col_ctrl2 = st.columns([1, 3])
    with col_ctrl1:
        lookback = st.selectbox("Historical Lookback Window (Weeks):", LOOKBACK_OPTIONS, index=LOOKBACK_OPTIONS.index(DEFAULT_LOOKBACK_WEEKS))
    m_df = compute_historical_extremes(m_df, series_col="primary_spec_net", lookback_window=lookback)

    # Check Price Alignment
    aligned_df = pd.DataFrame()
    has_price = False
    if commodity_label in ["Copper", "Silver", "Platinum"]:
        aligned_df = align_cot_and_price(m_df, commodity_label, convention="publication_aware")
        if not aligned_df.empty and 'price' in aligned_df.columns:
            has_price = True

    tabs = st.tabs([
        "🌊 Flow Decomposition & Weekly Returns",
        "📈 Positioning vs Price Momentum (4W, 8W, 13W, 26W)",
        "🎯 Historical Extremes & Price Trajectories"
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1: FLOW DECOMPOSITION & PRICE RESPONSE
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[0]:
        st.subheader("Weekly Position Decomposition (Speculative Flow Drivers) & Price Return")
        st.caption("Dissects weekly net positioning shifts into new long accumulation, short covering, liquidation, and new shorts, aligned with contemporaneous price returns.")

        c_t1, c_t2 = st.columns([3, 1])
        with c_t2:
            show_price_ret = st.checkbox("Overlay Weekly Price Return", value=has_price, disabled=not has_price)

        recent_df = aligned_df.tail(52).copy() if (has_price and not aligned_df.empty) else m_df.tail(52).copy()

        if show_price_ret and has_price:
            fig_decomp = make_subplots(specs=[[{"secondary_y": True}]])
        else:
            fig_decomp = go.Figure()

        # Decomposition Bars
        fig_decomp.add_trace(go.Bar(
            x=recent_df['report_date'], y=recent_df['decomp_long_acc'],
            name='Estimated Long Accumulation', marker_color=COLORS['long']
        ))
        fig_decomp.add_trace(go.Bar(
            x=recent_df['report_date'], y=recent_df['decomp_short_cov'],
            name='Estimated Short Covering', marker_color='#27ae60'
        ))
        fig_decomp.add_trace(go.Bar(
            x=recent_df['report_date'], y=recent_df['decomp_long_liq'],
            name='Estimated Long Liquidation', marker_color='#c0392b'
        ))
        fig_decomp.add_trace(go.Bar(
            x=recent_df['report_date'], y=recent_df['decomp_new_short'],
            name='Estimated New Shorts', marker_color=COLORS['short']
        ))
        fig_decomp.add_trace(go.Scatter(
            x=recent_df['report_date'], y=recent_df['delta_net'],
            mode='lines+markers', name='Net Weekly Change (ΔNet)', line=dict(color=COLORS['net'], width=2)
        ))

        # Price Return Overlay
        if show_price_ret and has_price and 'weekly_price_return' in recent_df.columns:
            fig_decomp.add_trace(
                go.Scatter(
                    x=recent_df['report_date'], y=recent_df['weekly_price_return'] * 100.0,
                    mode='lines+markers', name=f'{commodity_label} Weekly Return (%)',
                    line=dict(color='#fbc531', width=2.5)
                ),
                secondary_y=True
            )
            fig_decomp.update_yaxes(title_text="Weekly Price Return (%)", secondary_y=True, showgrid=False)
            fig_decomp.update_yaxes(title_text="Change in Contracts (WoW)", secondary_y=False)
        else:
            fig_decomp.update_layout(yaxis_title="Change in Contracts (WoW)")

        fig_decomp.update_layout(
            barmode='relative', template='plotly_dark', height=440,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation='h', y=1.06, x=0)
        )
        st.plotly_chart(fig_decomp, use_container_width=True)

        lat = recent_df.iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("ΔLong (This Week)", f"{lat['delta_long']:+,.0f} ctrs")
        with c2:
            st.metric("ΔShort (This Week)", f"{lat['delta_short']:+,.0f} ctrs")
        with c3:
            st.metric("ΔNet Spec (This Week)", f"{lat['delta_net']:+,.0f} ctrs")
        with c4:
            primary_driver = "Long Accumulation" if lat['delta_long'] > 0 and abs(lat['delta_long']) >= abs(lat['delta_short']) else \
                             "Short Covering" if lat['delta_short'] < 0 and abs(lat['delta_short']) > abs(lat['delta_long']) else \
                             "Long Liquidation" if lat['delta_long'] < 0 and abs(lat['delta_long']) >= abs(lat['delta_short']) else "New Short Formation"
            st.metric("Primary Flow Driver", primary_driver)

        st.markdown("""
        > [!NOTE]
        > **Flow Ingestion Methodology:** Flow components are mathematically inferred from weekly net changes in reported gross positions. They represent estimated aggregate volume reallocations, not directly observed tick-level exchange orders.
        """)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2: POSITIONING VS PRICE MOMENTUM
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[1]:
        st.subheader("Multi-Horizon Momentum: Positioning vs Price (4W, 8W, 13W, 26W)")
        st.caption("Investigates whether positioning velocity leads, lags, or co-moves with commodity price momentum across matching quarterly and multi-month horizons.")

        src_df = aligned_df if (has_price and not aligned_df.empty) else m_df

        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            sel_horizon = st.radio("Select Target Capital Horizon:", [4, 8, 13, 26], format_func=lambda x: f"{x}-Week Horizon", horizontal=True)
        with col_m2:
            overlay_price_mom = st.checkbox("Overlay Price Momentum", value=has_price, disabled=not has_price)

        mom_col = f"momentum_{sel_horizon}w"
        acc_col = f"accel_{sel_horizon}w"
        pmom_col = f"price_mom_{sel_horizon}w"

        if overlay_price_mom and has_price and pmom_col in src_df.columns:
            fig_mom = make_subplots(
                rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                row_heights=[0.6, 0.4],
                subplot_titles=[
                    f"{sel_horizon}-Week Momentum: COT Net Positioning vs {commodity_label} Price",
                    f"{sel_horizon}-Week Positioning Acceleration (ΔVelocity)"
                ],
                specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
            )
        else:
            fig_mom = make_subplots(
                rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                row_heights=[0.6, 0.4],
                subplot_titles=[
                    f"{sel_horizon}-Week Positioning Momentum (Contracts)",
                    f"{sel_horizon}-Week Positioning Acceleration (ΔVelocity)"
                ]
            )

        # Positioning Momentum Curve
        fig_mom.add_trace(go.Scatter(
            x=src_df['report_date'], y=src_df[mom_col],
            mode='lines', name=f'COT {sel_horizon}W Momentum',
            line=dict(color=COLORS['net'], width=2.2)
        ), row=1, col=1, secondary_y=False if (overlay_price_mom and has_price) else None)

        # Price Momentum Curve
        if overlay_price_mom and has_price and pmom_col in src_df.columns:
            fig_mom.add_trace(go.Scatter(
                x=src_df['report_date'], y=src_df[pmom_col] * 100.0,
                mode='lines', name=f'{commodity_label} {sel_horizon}W Price Return (%)',
                line=dict(color='#fbc531', width=2.0)
            ), row=1, col=1, secondary_y=True)
            fig_mom.update_yaxes(title_text=f"Price {sel_horizon}W Return (%)", row=1, col=1, secondary_y=True, showgrid=False)
            fig_mom.update_yaxes(title_text="Position Change (Contracts)", row=1, col=1, secondary_y=False)
        else:
            fig_mom.update_yaxes(title_text="Position Change (Contracts)", row=1, col=1)

        fig_mom.add_hline(y=0, line_dash='dash', line_color='gray', row=1, col=1)

        # Acceleration
        fig_mom.add_trace(go.Bar(
            x=src_df['report_date'], y=src_df[acc_col],
            name=f'{sel_horizon}W Acceleration (ΔVelocity)',
            marker_color=np.where(src_df[acc_col] >= 0, COLORS['long'], COLORS['short']),
            opacity=0.7
        ), row=2, col=1)
        fig_mom.add_hline(y=0, line_dash='dot', line_color='gray', row=2, col=1)
        fig_mom.update_yaxes(title_text="Δ Acceleration", row=2, col=1)

        fig_mom.update_layout(
            template='plotly_dark', height=480,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation='h', y=1.06, x=0)
        )
        st.plotly_chart(fig_mom, use_container_width=True)

        if has_price and pmom_col in src_df.columns:
            valid_m = src_df[[mom_col, pmom_col]].dropna()
            if len(valid_m) > 10:
                corr_val = valid_m[mom_col].corr(valid_m[pmom_col])
                st.info(f"**Empirical Co-Movement:** Rolling {sel_horizon}-Week Pearson correlation between Speculative Positioning Momentum and Commodity Price Momentum is **`r = {corr_val:+.3f}`**.")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3: HISTORICAL EXTREMES & PRICE CONTEXT
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[2]:
        st.subheader(f"Historical Positioning Extremes ({lookback}-Week Rolling Lookback) & Price Overlay")
        st.caption("Detects statistically over-extended positioning (|Z| > 2σ) and observes subsequent commodity price behavior.")

        src_df = aligned_df if (has_price and not aligned_df.empty) else m_df
        z_col = f"zscore_{lookback}w" if f"zscore_{lookback}w" in src_df.columns else "zscore_156w"
        pct_col = f"percentile_{lookback}w" if f"percentile_{lookback}w" in src_df.columns else "percentile_156w"

        if has_price and 'price' in src_df.columns:
            fig_z = make_subplots(
                rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                row_heights=[0.35, 0.35, 0.3],
                subplot_titles=[
                    f"Speculative Z-Score ({lookback}W Lookback)",
                    f"Percentile Rank ({lookback}W Lookback)",
                    f"{commodity_label} Physical Settlement Price ($) with Extreme Event Markers"
                ]
            )
        else:
            fig_z = make_subplots(
                rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                row_heights=[0.5, 0.5],
                subplot_titles=[f"Z-Score ({lookback}W)", f"Percentile ({lookback}W)"]
            )

        # Row 1: Z-Score
        fig_z.add_trace(go.Scatter(
            x=src_df['report_date'], y=src_df[z_col],
            mode='lines', name=f'Z-Score ({lookback}W)', line=dict(color=COLORS['net'], width=2)
        ), row=1, col=1)
        fig_z.add_hline(y=2.0, line_dash='dash', line_color=COLORS['short'], annotation_text='+2σ (Extreme Long)', row=1, col=1)
        fig_z.add_hline(y=-2.0, line_dash='dash', line_color=COLORS['long'], annotation_text='-2σ (Extreme Short)', row=1, col=1)
        fig_z.add_hline(y=0, line_dash='dot', line_color='gray', row=1, col=1)

        # Row 2: Percentile
        fig_z.add_trace(go.Scatter(
            x=src_df['report_date'], y=src_df[pct_col],
            mode='lines', name=f'Percentile ({lookback}W)', line=dict(color=COLORS['spread'], width=2)
        ), row=2, col=1)
        fig_z.add_hline(y=90.0, line_dash='dash', line_color=COLORS['short'], annotation_text='90% Pct', row=2, col=1)
        fig_z.add_hline(y=10.0, line_dash='dash', line_color=COLORS['long'], annotation_text='10% Pct', row=2, col=1)
        fig_z.add_hline(y=50.0, line_dash='dot', line_color='gray', row=2, col=1)

        # Row 3: Price with Extreme Markers
        if has_price and 'price' in src_df.columns:
            fig_z.add_trace(go.Scatter(
                x=src_df['report_date'], y=src_df['price'],
                mode='lines', name=f'{commodity_label} Price', line=dict(color='#fbc531', width=2)
            ), row=3, col=1)

            # High extremes markers
            hi_ev = src_df[src_df[z_col] >= 2.0]
            if not hi_ev.empty:
                fig_z.add_trace(go.Scatter(
                    x=hi_ev['report_date'], y=hi_ev['price'],
                    mode='markers', name='Extreme Long Event (Z >= +2σ)',
                    marker=dict(color='#eb4d4b', size=7, symbol='triangle-down')
                ), row=3, col=1)

            # Low extremes markers
            lo_ev = src_df[src_df[z_col] <= -2.0]
            if not lo_ev.empty:
                fig_z.add_trace(go.Scatter(
                    x=lo_ev['report_date'], y=lo_ev['price'],
                    mode='markers', name='Extreme Short Event (Z <= -2σ)',
                    marker=dict(color='#2ecc71', size=7, symbol='triangle-up')
                ), row=3, col=1)

            fig_z.update_yaxes(title_text="Price ($)", row=3, col=1)

        fig_z.update_layout(
            template='plotly_dark', height=560 if has_price else 450,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation='h', y=1.05, x=0)
        )
        st.plotly_chart(fig_z, use_container_width=True)

        lat_z = src_df[z_col].iloc[-1]
        lat_pct = src_df[pct_col].iloc[-1]
        
        with st.expander("ℹ️ Công thức tính & Mục đích sử dụng: Z-Score & Percentile Extremes", expanded=False):
            st.markdown(r"""
            ##### 1. Rolling Z-Score
            - **Công thức:** 
              $$Z_t = \frac{Pos_t - \mu_{t, W}}{\sigma_{t, W}}$$
              *Trong đó $Pos_t$ là vị thế ròng Managed Money tuần $t$, $\mu_{t, W}$ và $\sigma_{t, W}$ là giá trị trung bình và độ lệch chuẩn rolling trong cửa sổ $W$ tuần (mặc định 52 tuần).*
            - **Mục đích:** Chuẩn hóa vị thế về số độ lệch chuẩn ($\sigma$). Giúp so sánh mức độ căng cứng của vị thế độc lập với quy mô tăng trưởng của thị trường. Ngưỡng $|Z| \ge 2.0\sigma$ phản ánh trạng thái quá mua/quá bán thống kê (chỉ xảy ra ~5% thời gian).

            ##### 2. Rolling Percentile (COT Index)
            - **Công thức:**
              $$Percentile_t = \frac{Pos_t - \min(Pos_W)}{\max(Pos_W) - \min(Pos_W)} \times 100\%$$
            - **Mục đích:** Xếp hạng vị thế hiện tại so với biên độ cao nhất / thấp nhất trong chu kỳ $W$ tuần. Ngưỡng $>90\%$ báo hiệu vị thế gom mua chạm trần lịch sử, $<10\%$ báo hiệu phe bán đã ép cạn kiệt.
            """)

        col_z1, col_z2 = st.columns(2)
        with col_z1:
            st.metric(
                f"Rolling Z-Score ({lookback}W)", f"{lat_z:+.2f} Std",
                help="Công thức: (Vị thế hiện tại - Trung bình W tuần) / Độ lệch chuẩn W tuần.\nMục đích: Đo độ lệch chuẩn hóa. Z > +2: Quá mua cực đoan; Z < -2: Quá bán cực đoan."
            )
        with col_z2:
            st.metric(
                f"Rolling Percentile ({lookback}W)", f"{lat_pct:.1f}%",
                help="Công thức: (Vị thế - Min) / (Max - Min) * 100% trong W tuần.\nMục đích: Xếp hạng vị trí tương đối của vị thế trong chu kỳ."
            )

        st.markdown(f"""
        **Current Statistical Assessment:**
        - **Diagnosis:** {'🔴 Extreme Long Overhang (> +2.0 Std) — Speculative extension' if lat_z >= 2.0 else '🟢 Extreme Short Overhang (< -2.0 Std) — Speculative exhaustion' if lat_z <= -2.0 else '⚪ Neutral Corridor (|Z| < 2.0 Std) — Balanced liquidity'}
        """)
