"""
COT DATA RESEARCH LAB — MULTI-REPORT COMMODITY RESEARCH PLATFORM
================================================================
Institutional Quantitative Research Workstation for CFTC Positioning Data.
Analytical and Educational Platform (Strictly Non-Trading).
"""

import streamlit as st
import pandas as pd
import datetime

# Configure Streamlit page for maximum width and institutional dark feel
st.set_page_config(
    page_title="COT Data Research Lab",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Institutional CSS
st.markdown("""
<style>
    /* Dark institutional styling */
    .stApp {
        background-color: #0b0e14;
        color: #f1f2f6;
    }
    div[data-testid="stSidebar"] {
        background-color: #121721;
        border-right: 1px solid #1f2737;
    }
    .metric-card {
        background-color: #161c28;
        border: 1px solid #232d3f;
        border-radius: 6px;
        padding: 12px;
    }
    /* Dense table font */
    div[data-testid="stDataFrame"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# Imports from modular research_lab package
from research_lab.config import TARGET_COMMODITIES, COLORS
from research_lab.data_loader import (
    load_raw_disaggregated,
    load_raw_tff,
    load_verified_prices,
    get_market_series
)
from research_lab.market_registry import build_market_registry
from research_lab.views.view_overview import render_overview
from research_lab.views.view_explorer import render_explorer
from research_lab.views.view_trader_analysis import render_trader_analysis
from research_lab.views.view_positioning import render_positioning_dynamics
from research_lab.views.view_statistics import render_statistics
from research_lab.views.view_evaluation import render_evaluation
from research_lab.views.view_knowledge import render_knowledge_base
from research_lab.views.view_reports import render_reports
from research_lab.views.view_data_center import render_data_center

# ─────────────────────────────────────────────────────────────────────────────
# 1. DATA INGESTION & REGISTRY INITIALIZATION (CACHED)
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner("Initializing COT Research Lab Data Infrastructure..."):
    df_disagg = load_raw_disaggregated()
    df_tff = load_raw_tff()
    price_df = load_verified_prices()
    reg_disagg = build_market_registry(df_disagg, "Disaggregated COT")
    reg_tff = build_market_registry(df_tff, "TFF COT")

# ─────────────────────────────────────────────────────────────────────────────
# 2. SIDEBAR NAVIGATION & GLOBAL CONTROLS
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style="padding: 10px 0; border-bottom: 1px solid #232d3f; margin-bottom: 15px;">
    <h3 style="margin: 0; color: #4bcffa; font-size: 18px; letter-spacing: 0.5px;">COT RESEARCH LAB</h3>
    <p style="margin: 3px 0 0 0; font-size: 11px; color: #a4b0be;">Institutional Commodity Workstation</p>
</div>
""", unsafe_allow_html=True)

MODULES = [
    "1. Overview & Data Coverage",
    "2. Market Explorer & Dictionary",
    "3. Trader Behavior Analysis",
    "4. Positioning Dynamics & Flow",
    "5. Statistical Research & Tests",
    "6. COT & Price Relationship Lab",
    "7. Applications & Knowledge Base",
    "8. Research Report Workspace",
    "9. Data Center & Export Hub"
]

selected_module = st.sidebar.radio("Navigation:", MODULES, index=0)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Global Research Context")

# Report Family Selector (Disaggregated vs TFF kept strictly separate)
report_family = st.sidebar.selectbox(
    "Report Family:",
    ["Disaggregated COT (Primary - Commodities)", "Traders in Financial Futures (TFF)"]
)

is_disagg = "Disaggregated" in report_family
active_df = df_disagg if is_disagg else df_tff
active_reg = reg_disagg if is_disagg else reg_tff
report_family_name = "Disaggregated COT" if is_disagg else "TFF COT"

# Commodity / Market Selector
if is_disagg:
    target_names = ["Copper", "Silver", "Platinum", "Micro Copper", "Micro Silver", "--- All Other Markets ---"]
    sel_target = st.sidebar.selectbox("Commodity Selection:", target_names)
    
    if sel_target in TARGET_COMMODITIES:
        target_info = TARGET_COMMODITIES[sel_target]
        contract_code = target_info['code']
        commodity_label = sel_target
    else:
        other_markets = active_reg['market_name'].unique().tolist()
        sel_market_name = st.sidebar.selectbox("Select Contract Market:", other_markets)
        sub_row = active_reg[active_reg['market_name'] == sel_market_name].iloc[0]
        contract_code = sub_row['contract_code']
        commodity_label = sub_row['commodity']
else:
    tff_markets = active_reg['market_name'].unique().tolist()
    sel_market_name = st.sidebar.selectbox("Select Financial Market:", tff_markets)
    sub_row = active_reg[active_reg['market_name'] == sel_market_name].iloc[0]
    contract_code = sub_row['contract_code']
    commodity_label = sub_row['commodity']

# Extract selected market series
market_df = get_market_series(active_df, contract_code)

# Global Date Range Filter
if not market_df.empty:
    min_date = market_df['report_date'].min().date()
    max_date = market_df['report_date'].max().date()
    date_range = st.sidebar.date_input(
        "Date Range Filter:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        market_df = market_df[
            (market_df['report_date'].dt.date >= date_range[0]) &
            (market_df['report_date'].dt.date <= date_range[1])
        ]

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="font-size: 11px; color: #778ca3; line-height: 1.5;">
    <b>Source Status:</b> Verified<br/>
    <b>Classification:</b> {report_family_name}<br/>
    <b>Report Format:</b> Combined Only<br/>
    <b>Target Code:</b> <code>{contract_code}</code><br/>
    <b>Filtered Obs:</b> {len(market_df)} weeks
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 3. ROUTE TO MODULAR VIEW
# ─────────────────────────────────────────────────────────────────────────────
if selected_module == "1. Overview & Data Coverage":
    render_overview(df_disagg, df_tff, reg_disagg, reg_tff)

elif selected_module == "2. Market Explorer & Dictionary":
    render_explorer(active_reg, report_family_name)

elif selected_module == "3. Trader Behavior Analysis":
    render_trader_analysis(market_df, report_family_name, commodity_label, price_df)

elif selected_module == "4. Positioning Dynamics & Flow":
    render_positioning_dynamics(market_df, report_family_name, commodity_label, price_df)

elif selected_module == "5. Statistical Research & Tests":
    render_statistics(market_df, report_family_name, commodity_label, df_disagg)

elif selected_module == "6. COT & Price Relationship Lab":
    render_evaluation(market_df, report_family_name, commodity_label, price_df)

elif selected_module == "7. Applications & Knowledge Base":
    render_knowledge_base()

elif selected_module == "8. Research Report Workspace":
    render_reports(commodity_label, report_family_name, contract_code, market_df, price_df)

elif selected_module == "9. Data Center & Export Hub":
    render_data_center(market_df, report_family_name, commodity_label, price_df, df_disagg, df_tff)

