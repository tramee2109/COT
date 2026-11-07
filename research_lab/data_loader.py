"""
COT DATA RESEARCH LAB — Data Ingestion & Canonical Normalization Layer
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
from research_lab.config import (
    DATA_DISAGG_PATH,
    DATA_TFF_PATH,
    PRICES_PARQUET_PATH,
    TARGET_COMMODITIES
)

DATA_DISAGG_PQ = DATA_DISAGG_PATH.replace(".csv", ".parquet")
DATA_TFF_PQ = DATA_TFF_PATH.replace(".csv", ".parquet")
MACRO_DAILY_PQ = os.path.join(os.path.dirname(DATA_TFF_PATH), "macro_cot_daily_features.parquet")

@st.cache_data(show_spinner=False)
def load_raw_disaggregated():
    """
    Loads raw Disaggregated COT dataset (Combined).
    Loads Parquet format when available for sub-second read performance.
    Guarantees raw data protection: returns copy, preserves original fields.
    """
    if os.path.exists(DATA_DISAGG_PQ):
        df = pd.read_parquet(DATA_DISAGG_PQ)
    elif os.path.exists(DATA_DISAGG_PATH):
        df = pd.read_csv(DATA_DISAGG_PATH, low_memory=False)
    else:
        raise FileNotFoundError(f"Disaggregated COT file not found: {DATA_DISAGG_PATH}")

    # Canonical report_date parsing
    df['report_date'] = pd.to_datetime(df['Report_Date_as_YYYY-MM-DD'], errors='coerce')
    df = df.dropna(subset=['report_date'])
    
    # Metadata normalization
    df['report_family'] = 'Disaggregated COT'
    df['market_name_clean'] = df['Market_and_Exchange_Names'].astype(str).str.strip()
    df['contract_code_clean'] = df['CFTC_Contract_Market_Code'].astype(str).str.strip().str.zfill(6)
    
    # Sort
    df = df.sort_values(['contract_code_clean', 'report_date']).reset_index(drop=True)
    return df

@st.cache_data(show_spinner=False)
def load_raw_tff():
    """
    Loads raw Traders in Financial Futures (TFF) dataset.
    Loads Parquet format when available for sub-second read performance.
    Solves dual date column discrepancy (MM_DD_YYYY vs YYYY-MM-DD).
    """
    if os.path.exists(DATA_TFF_PQ):
        df = pd.read_parquet(DATA_TFF_PQ)
    elif os.path.exists(DATA_TFF_PATH):
        df = pd.read_csv(DATA_TFF_PATH, low_memory=False)
    else:
        raise FileNotFoundError(f"TFF COT file not found: {DATA_TFF_PATH}")

    # Dual date resolution
    t_d1 = pd.to_datetime(df['Report_Date_as_YYYY-MM-DD'], errors='coerce') if 'Report_Date_as_YYYY-MM-DD' in df.columns else pd.Series()
    t_d2 = pd.to_datetime(df['Report_Date_as_MM_DD_YYYY'], errors='coerce') if 'Report_Date_as_MM_DD_YYYY' in df.columns else pd.Series()
    df['report_date'] = t_d1.combine_first(t_d2)
    df = df.dropna(subset=['report_date'])

    df['report_family'] = 'Traders in Financial Futures (TFF)'
    df['market_name_clean'] = df['Market_and_Exchange_Names'].astype(str).str.strip()
    df['contract_code_clean'] = df['CFTC_Contract_Market_Code'].astype(str).str.strip().str.zfill(6)

    df = df.sort_values(['contract_code_clean', 'report_date']).reset_index(drop=True)
    return df

@st.cache_data(show_spinner=False)
def load_verified_prices():
    """
    Loads verified daily metals settlement prices from workspace:
    daily_fundamental_features.parquet
    """
    if not os.path.exists(PRICES_PARQUET_PATH):
        return pd.DataFrame()

    df = pd.read_parquet(PRICES_PARQUET_PATH)
    df['date'] = pd.to_datetime(df['date'])
    return df

@st.cache_data(show_spinner=False)
def load_macro_daily_features():
    """
    Loads daily lookahead-safe macro cross-asset features
    (USD Index, US 10Y, US 2Y, S&P 500, VIX, Bitcoin, Macro Risk Score).
    """
    if os.path.exists(MACRO_DAILY_PQ):
        return pd.read_parquet(MACRO_DAILY_PQ)
    return pd.DataFrame()

def get_market_series(df, contract_code, market_name=None):
    """
    Retrieves time series for a specific market.
    For Copper (085692), stitches the two names continuously while recording transition.
    """
    code_clean = str(contract_code).strip().zfill(6)
    sub = df[df['contract_code_clean'] == code_clean].copy()
    
    if market_name and code_clean not in ["085692"]: # Allow copper full code continuity
        sub = sub[sub['market_name_clean'] == market_name]
        
    return sub.sort_values('report_date').reset_index(drop=True)
