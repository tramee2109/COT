"""
COT DATA RESEARCH LAB — Module 5: Statistical Research & Econometrics
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from research_lab.config import COLORS
from research_lab.metrics_engine import compute_trader_metrics
from research_lab.statistical_engine import (
    compute_descriptive_stats,
    perform_stationarity_test,
    compute_autocorrelations,
    compute_trader_correlation_matrix,
    compute_cross_commodity_comparison
)

def render_statistics(market_df, report_family_name, commodity_label, df_all_disagg):
    st.title(f"📐 Statistical Research & Econometrics — {commodity_label}")
    st.caption("Investigate empirical distributions, stationarity, autocorrelation decay, and cross-commodity correlations.")

    if market_df.empty:
        st.warning("No data available for the selected market.")
        return

    m_df = compute_trader_metrics(market_df, report_family_name)

    tabs = st.tabs(["📊 Distribution & Descriptives", "⏱️ Time-Series & Stationarity (ADF)", "🔄 Trader Correlation Matrix", "🌐 Cross-Commodity Relative Analysis"])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1: DISTRIBUTION & DESCRIPTIVES
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[0]:
        st.subheader("Empirical Distribution Analysis")
        st.caption("Assess skewness, tail kurtosis, and non-normality in speculative positioning.")

        series_map = {
            "Managed Money Net Position": "primary_spec_net",
            "Managed Money % of Open Interest": "managed_money_net_pct_oi" if "Disaggregated" in report_family_name else "lev_money_net_pct_oi",
            "Producer / Commercial Net Position": "primary_commercial_net",
            "Total Open Interest": "Open_Interest_All"
        }
        sel_sname = st.selectbox("Select Variable for Distribution Analysis:", list(series_map.keys()))
        s_col = series_map[sel_sname]
        data_s = m_df[s_col].dropna()

        # Stats Table
        stats_dict = compute_descriptive_stats(data_s, name=sel_sname)
        stats_df = pd.DataFrame([stats_dict])
        
        st.dataframe(
            stats_df.style.format({
                "Mean": "{:,.1f}", "Median": "{:,.1f}", "Std Dev": "{:,.1f}",
                "Min": "{:,.1f}", "Max": "{:,.1f}", "Skewness": "{:+.3f}",
                "Excess Kurtosis": "{:+.3f}", "IQR": "{:,.1f}",
                "25th Pct": "{:,.1f}", "75th Pct": "{:,.1f}"
            }),
            use_container_width=True
        )

        col_hist, col_box = st.columns([2, 1])
        with col_hist:
            fig_dist = px.histogram(
                m_df, x=s_col, nbins=35, marginal="rug",
                title=f"Histogram & Empirical Frequency ({sel_sname})",
                color_discrete_sequence=[COLORS['net']]
            )
            fig_dist.update_layout(template='plotly_dark', height=360, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_dist, use_container_width=True)

        with col_box:
            fig_box = px.box(
                m_df, y=s_col, points="outliers",
                title=f"Boxplot & Outliers",
                color_discrete_sequence=[COLORS['spread']]
            )
            fig_box.update_layout(template='plotly_dark', height=360, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_box, use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2: TIME-SERIES & STATIONARITY
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[1]:
        st.subheader("Time-Series Diagnostics: Autocorrelation & Stationarity")
        st.caption("Distinguishes raw position levels (often non-stationary) from weekly changes (stationary).")

        use_diff = st.radio("Evaluate Variable in:", ["Level (Raw Value)", "Weekly First Difference (Δ Change)"], horizontal=True)
        eval_series = m_df['primary_spec_net'].diff(1).dropna() if "Difference" in use_diff else m_df['primary_spec_net'].dropna()

        # ADF Test
        st.markdown("#### 1. Augmented Dickey-Fuller (ADF) Unit Root Test")
        adf_res = perform_stationarity_test(eval_series)
        
        c_adf1, c_adf2, c_adf3, c_adf4 = st.columns(4)
        with c_adf1:
            st.metric(
                "ADF Test Statistic", f"{adf_res['adf_statistic']:.3f}",
                help="Công thức: Giá trị thống kê kiểm định t từ phương trình hồi quy ADF:\nΔy_t = α + β*t + γ*y_{t-1} + Σ δ_i*Δy_{t-i} + ε_t.\nMục đích: Kiểm định xem chuỗi có nghiệm đơn vị (Unit Root) hay không. Càng âm sâu dưới giá trị tới hạn (Critical Value) thì chuỗi càng dừng (stationary)."
            )
        with c_adf2:
            st.metric(
                "p-value", f"{adf_res['p_value']:.4f}",
                help="Công thức: Xác suất MacKinnon p-value đối với giả thuyết không (H0: Chuỗi không dừng - có unit root).\nMục đích: Nếu p-value < 0.05, bác bỏ giả thuyết H0, kết luận chuỗi có tính dừng (Stationary), thích hợp để đưa vào các mô hình định lượng mà không sợ tương quan giả."
            )
        with c_adf3:
            st.metric(
                "5% Critical Value", f"{adf_res['crit_5pct']:.3f}",
                help="Giá trị ngưỡng tới hạn ở mức ý nghĩa thống kê 5%. Nếu ADF Statistic < Critical Value này, chuỗi đạt tính dừng ở độ tin cậy 95%."
            )
        with c_adf4:
            st.metric(
                "Stationarity Status", "Stationary" if adf_res['is_stationary_5pct'] else "Non-Stationary",
                help="Kết luận tính dừng (Stationary vs Non-Stationary). Dữ liệu vị thế gốc (Levels) thường không dừng, còn biến thiên hàng tuần (Δ Change) luôn có tính dừng."
            )

        st.info(f"**Econometric Conclusion:** {adf_res['conclusion']}. Note: Level positioning typically exhibits strong autocorrelation (unit root present), meaning classical regression on raw levels can yield spurious correlations. Differenced weekly changes should be used for return regression.")

        # ACF & PACF
        st.markdown("#### 2. Autocorrelation (ACF) & Partial Autocorrelation (PACF) Decay")
        acf_df = compute_autocorrelations(eval_series, nlags=16)
        if not acf_df.empty:
            fig_acf = make_subplots(rows=1, cols=2, subplot_titles=["Autocorrelation (ACF)", "Partial Autocorrelation (PACF)"])
            fig_acf.add_trace(go.Bar(
                x=acf_df['Lag'], y=acf_df['ACF'], marker_color=COLORS['net'], name='ACF'
            ), row=1, col=1)
            fig_acf.add_trace(go.Bar(
                x=acf_df['Lag'], y=acf_df['PACF'], marker_color=COLORS['managed_money'], name='PACF'
            ), row=1, col=2)
            fig_acf.add_hline(y=0.1, line_dash='dash', line_color='gray', opacity=0.5)
            fig_acf.add_hline(y=-0.1, line_dash='dash', line_color='gray', opacity=0.5)
            fig_acf.update_layout(template='plotly_dark', height=320, margin=dict(l=20, r=20, t=40, b=20), showlegend=False)
            st.plotly_chart(fig_acf, use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3: TRADER CORRELATION MATRIX
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[2]:
        st.subheader("Cross-Category Correlation Matrix")
        st.caption("Empirical correlation of positioning across participant categories.")

        corr_mode = st.radio("Correlation Basis:", ["Weekly Changes (Δ) — Econometrically Robust", "Raw Levels — Measures Structural Offset"], horizontal=True)
        corr_matrix = compute_trader_correlation_matrix(
            m_df, report_family=report_family_name, use_changes=("Weekly Changes" in corr_mode)
        )

        fig_heat = px.imshow(
            corr_matrix, text_auto=".2f", aspect="auto",
            color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
            title=f"Trader Correlation Heatmap ({corr_mode})"
        )
        fig_heat.update_layout(template='plotly_dark', height=400, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_heat, use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 4: CROSS-COMMODITY RELATIVE ANALYSIS
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[3]:
        st.subheader("Cross-Commodity Positioning Comparison (Copper, Silver, Platinum)")
        st.caption("Standardized Speculative Net % of OI across primary industrial and precious metals.")

        cross_df = compute_cross_commodity_comparison(df_all_disagg, metric="managed_money_net_pct_oi")
        if not cross_df.empty:
            fig_cross = go.Figure()
            col_list = [COLORS['net'], COLORS['text_primary'], COLORS['spread']]
            for i, col_name in enumerate(cross_df.columns):
                fig_cross.add_trace(go.Scatter(
                    x=cross_df.index, y=cross_df[col_name],
                    mode='lines', name=col_name, line=dict(color=col_list[i % len(col_list)], width=2)
                ))
            fig_cross.add_hline(y=0, line_dash='dash', line_color='gray')
            fig_cross.update_layout(
                template='plotly_dark', height=400,
                margin=dict(l=20, r=20, t=30, b=20),
                yaxis_title="Managed Money Net (% of Open Interest)",
                legend=dict(orientation='h', y=1.05, x=0)
            )
            st.plotly_chart(fig_cross, use_container_width=True)

            st.markdown("#### Pairwise Cross-Commodity Correlation")
            st.dataframe(cross_df.corr().style.format("{:+.2f}"), use_container_width=True)
        else:
            st.info("Cross-commodity data comparison requires Disaggregated COT dataset.")

