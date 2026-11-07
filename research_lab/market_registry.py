"""
COT DATA RESEARCH LAB — Dynamic Market Registry Builder
"""

import streamlit as st
import pandas as pd
import numpy as np
from research_lab.config import TARGET_COMMODITIES

@st.cache_data(show_spinner=False)
def build_market_registry(df, report_family_name):
    """
    Constructs a comprehensive, dynamic market registry directly from actual dataset.
    """
    records = []
    grouped = df.groupby('contract_code_clean')

    for code, g in grouped:
        names = g['market_name_clean'].unique().tolist()
        primary_name = names[-1] # Latest market name
        
        d_min = g['report_date'].min()
        d_max = g['report_date'].max()
        n_obs = len(g)
        
        # Calculate expected weekly observations
        total_weeks = max(1, int(np.round((d_max - d_min).days / 7.0)) + 1)
        completeness = min(100.0, (n_obs / total_weeks) * 100.0)
        
        # Exchange extraction
        exchange = "UNKNOWN"
        if " - " in primary_name:
            exchange = primary_name.split(" - ")[-1]
            
        # Target commodity classification
        target_status = "General Market"
        commodity_label = primary_name.split(" - ")[0]
        
        for t_name, t_meta in TARGET_COMMODITIES.items():
            if code == t_meta['code']:
                target_status = f"Target Commodity ({t_name})"
                commodity_label = t_name
                break
                
        records.append({
            "contract_code": code,
            "commodity": commodity_label,
            "market_name": primary_name,
            "all_historical_names": names,
            "exchange": exchange,
            "report_family": report_family_name,
            "report_format": "Combined",
            "first_date": d_min.strftime('%Y-%m-%d'),
            "last_date": d_max.strftime('%Y-%m-%d'),
            "observation_count": n_obs,
            "completeness_pct": round(completeness, 1),
            "status": target_status
        })

    reg_df = pd.DataFrame(records)
    return reg_df.sort_values(['status', 'observation_count'], ascending=[False, False]).reset_index(drop=True)

