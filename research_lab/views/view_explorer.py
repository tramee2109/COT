"""
COT DATA RESEARCH LAB — Module 2: Market Explorer & Schema Data Dictionary
"""

import streamlit as st
import pandas as pd
from research_lab.data_dictionary import get_data_dictionary

def render_explorer(reg_df, report_family_name):
    st.title("🔍 Market Explorer & Schema Dictionary")
    st.caption("Interactive Screener and Official CFTC Technical Data Dictionary")

    tab_explorer, tab_dict = st.tabs(["📊 Interactive Market Screener", "📖 Schema Data Dictionary"])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1: MARKET SCREENER
    # ─────────────────────────────────────────────────────────────────────────
    with tab_explorer:
        st.subheader(f"Contract Market Directory — {report_family_name}")
        st.caption(f"Explore all {len(reg_df)} distinct contract markets present in the verified dataset.")

        c_search, c_filter, c_exc = st.columns([2, 1, 1])
        with c_search:
            search_query = st.text_input("Search market name or commodity:", placeholder="e.g. Copper, Silver, Crude, Corn...")
        with c_filter:
            status_filter = st.selectbox("Status Filter:", ["All Markets", "Target Commodities Only", "Major Markets (>200 Obs)"])
        with c_exc:
            all_exchanges = ["All Exchanges"] + sorted(reg_df['exchange'].unique().tolist())
            exc_filter = st.selectbox("Exchange:", all_exchanges)

        filtered = reg_df.copy()
        if search_query:
            q = search_query.strip().lower()
            filtered = filtered[
                filtered['market_name'].str.lower().str.contains(q) |
                filtered['commodity'].str.lower().str.contains(q) |
                filtered['contract_code'].str.contains(q)
            ]

        if status_filter == "Target Commodities Only":
            filtered = filtered[filtered['status'].str.contains("Target")]
        elif status_filter == "Major Markets (>200 Obs)":
            filtered = filtered[filtered['observation_count'] >= 200]

        if exc_filter != "All Exchanges":
            filtered = filtered[filtered['exchange'] == exc_filter]

        st.dataframe(
            filtered[[
                'contract_code', 'commodity', 'market_name', 'exchange',
                'first_date', 'last_date', 'observation_count', 'completeness_pct', 'status'
            ]].rename(columns={
                'contract_code': 'Contract Code',
                'commodity': 'Commodity',
                'market_name': 'Official Market Name',
                'exchange': 'Exchange',
                'first_date': 'First Obs',
                'last_date': 'Latest Obs',
                'observation_count': 'Total Obs',
                'completeness_pct': 'Completeness %',
                'status': 'Category Status'
            }),
            use_container_width=True,
            height=420
        )
        st.caption(f"Showing {len(filtered)} of {len(reg_df)} markets.")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2: DATA DICTIONARY
    # ─────────────────────────────────────────────────────────────────────────
    with tab_dict:
        st.subheader(f"Official CFTC Data Dictionary ({report_family_name})")
        st.caption("Authoritative definitions, computational formulas, economic interpretations, and common pitfalls.")

        dict_df = get_data_dictionary(report_family_name)
        
        c_cat, c_kw = st.columns([1, 2])
        with c_cat:
            cats = ["All Categories"] + sorted(dict_df['category'].unique().tolist())
            sel_cat = st.selectbox("Field Category:", cats)
        with c_kw:
            kw = st.text_input("Filter definitions by keyword:", placeholder="e.g. Managed Money, Swap, Open Interest...")

        filtered_dict = dict_df.copy()
        if sel_cat != "All Categories":
            filtered_dict = filtered_dict[filtered_dict['category'] == sel_cat]
        if kw:
            q_kw = kw.strip().lower()
            filtered_dict = filtered_dict[
                filtered_dict['column'].str.lower().str.contains(q_kw) |
                filtered_dict['label'].str.lower().str.contains(q_kw) |
                filtered_dict['definition'].str.lower().str.contains(q_kw)
            ]

        for _, r in filtered_dict.iterrows():
            with st.expander(f"📌 {r['label']}  —  `{r['column']}` ({r['category']})"):
                st.markdown(f"**Field Type:** `{r['type']}` | **Unit:** `{r['unit']}` | **Trader Group:** `{r['trader_group']}`")
                st.markdown(f"**CFTC Official Definition:** {r['definition']}")
                if r['formula'] != "None":
                    st.markdown(f"**Computational Formula:** `{r['formula']}`")
                st.markdown(f"**Economic Interpretation:** {r['interpretation']}")
                st.markdown(f"⚠️ **Common Pitfall / Risk:** {r['pitfall']}")

