"""
COT Quantitative Feature Engineering & Signal Engine
=====================================================
Calculates quantitative metrics, market regimes, and signals from CFTC COT data:
- TFF (Traders in Financial Futures)
- Disaggregated Commodities (Agriculture, Energy, Metals)

Provides:
- Net speculative positioning & % of Open Interest
- COT Index (1Y and 3Y percentile range [0, 100])
- Rolling Z-Score (standardized deviation)
- Crowding Index (% Long of speculative money)
- Commercial Hedging Pressure
- Institutional Flow Momentum (1W and 4W)
- Market Regime Classification (Extreme Long, Extreme Short, Accumulation, Distribution)
- Lookahead-Safe Daily Resampling (aligns Tuesday reports to actionable Monday trading dates)
"""

import os
import glob
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_TFF_DIR = os.path.join(BASE_DIR, "data")
DATA_DISAGG_DIR = os.path.join(BASE_DIR, "data_disaggregated")

# ─────────────────────────────────────────────────────────────────────────────
# 1. LOAD & PROCESS TFF DATA (Financial Futures, Rates, FX, Gold, Oil)
# ─────────────────────────────────────────────────────────────────────────────
def load_tff_data():
    files = sorted(glob.glob(os.path.join(DATA_TFF_DIR, "cot_20*.csv")))
    files = [f for f in files if "cot_full" not in os.path.basename(f)]
    if not files:
        return pd.DataFrame()

    dfs = [pd.read_csv(f, low_memory=False) for f in files]
    df = pd.concat(dfs, ignore_index=True)

    date_col = 'Report_Date_as_YYYY-MM-DD' if 'Report_Date_as_YYYY-MM-DD' in df.columns else 'Report_Date_as_MM_DD_YYYY'
    
    needed_cols = [
        'Market_and_Exchange_Names', date_col,
        'Open_Interest_All', 'Change_in_Open_Interest_All',
        'Dealer_Positions_Long_All', 'Dealer_Positions_Short_All',
        'Asset_Mgr_Positions_Long_All', 'Asset_Mgr_Positions_Short_All',
        'Lev_Money_Positions_Long_All', 'Lev_Money_Positions_Short_All',
        'Other_Rept_Positions_Long_All', 'Other_Rept_Positions_Short_All',
        'NonRept_Positions_Long_All', 'NonRept_Positions_Short_All'
    ]
    avail_cols = [c for c in needed_cols if c in df.columns]
    df = df[avail_cols].copy()

    df['Date'] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=['Date'])

    num_cols = [c for c in avail_cols if c not in ['Market_and_Exchange_Names', date_col]]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')

    df['Market'] = df['Market_and_Exchange_Names'].str.strip()
    df = df.sort_values(['Market', 'Date']).reset_index(drop=True)

    # Derived Positioning
    df['AssetMgr_Net'] = df['Asset_Mgr_Positions_Long_All'] - df['Asset_Mgr_Positions_Short_All']
    df['LevMoney_Net'] = df['Lev_Money_Positions_Long_All'] - df['Lev_Money_Positions_Short_All']
    df['Dealer_Net']   = df['Dealer_Positions_Long_All']    - df['Dealer_Positions_Short_All']
    df['NonRept_Net']  = df['NonRept_Positions_Long_All']   - df['NonRept_Positions_Short_All']
    df['Net_Spec']     = df['AssetMgr_Net'] + df['LevMoney_Net']
    df['Net_Spec_Pct_OI'] = df['Net_Spec'] / df['Open_Interest_All'].replace(0, np.nan)

    lm_gross = df['Lev_Money_Positions_Long_All'] + df['Lev_Money_Positions_Short_All']
    df['Crowding_Index'] = (df['Lev_Money_Positions_Long_All'] / lm_gross.replace(0, np.nan)) * 100

    df['Report_Type'] = 'TFF'
    return df

# ─────────────────────────────────────────────────────────────────────────────
# 2. LOAD & PROCESS DISAGGREGATED DATA (Physical Commodities)
# ─────────────────────────────────────────────────────────────────────────────
def load_disaggregated_data():
    files = sorted(glob.glob(os.path.join(DATA_DISAGG_DIR, "cot_disagg_20*.csv")))
    files = [f for f in files if "cot_disagg_full" not in os.path.basename(f)]
    if not files:
        return pd.DataFrame()

    dfs = [pd.read_csv(f, low_memory=False) for f in files]
    df = pd.concat(dfs, ignore_index=True)

    date_col = 'Report_Date_as_YYYY-MM-DD' if 'Report_Date_as_YYYY-MM-DD' in df.columns else 'Report_Date_as_MM_DD_YYYY'

    needed_cols = [
        'Market_and_Exchange_Names', date_col,
        'Open_Interest_All', 'Change_in_Open_Interest_All',
        'Prod_Merc_Positions_Long_All', 'Prod_Merc_Positions_Short_All',
        'Swap_Positions_Long_All', 'Swap__Positions_Short_All',
        'M_Money_Positions_Long_All', 'M_Money_Positions_Short_All',
        'Other_Rept_Positions_Long_All', 'Other_Rept_Positions_Short_All',
        'NonRept_Positions_Long_All', 'NonRept_Positions_Short_All'
    ]
    avail_cols = [c for c in needed_cols if c in df.columns]
    df = df[avail_cols].copy()

    df['Date'] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=['Date'])

    num_cols = [c for c in avail_cols if c not in ['Market_and_Exchange_Names', date_col]]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')

    df['Market'] = df['Market_and_Exchange_Names'].str.strip()
    df = df.sort_values(['Market', 'Date']).reset_index(drop=True)

    # Derived Positioning for Commodities
    df['Commercial_Net'] = df['Prod_Merc_Positions_Long_All'] - df['Prod_Merc_Positions_Short_All']
    df['Managed_Money_Net'] = df['M_Money_Positions_Long_All'] - df['M_Money_Positions_Short_All']
    df['Swap_Net'] = df['Swap_Positions_Long_All'] - df['Swap__Positions_Short_All']
    
    # Net_Spec in Commodities is Managed Money Net
    df['Net_Spec'] = df['Managed_Money_Net']
    df['Net_Spec_Pct_OI'] = df['Net_Spec'] / df['Open_Interest_All'].replace(0, np.nan)

    mm_gross = df['M_Money_Positions_Long_All'] + df['M_Money_Positions_Short_All']
    df['Crowding_Index'] = (df['M_Money_Positions_Long_All'] / mm_gross.replace(0, np.nan)) * 100
    df['Commercial_Pressure'] = (df['Commercial_Net'] / df['Open_Interest_All'].replace(0, np.nan)) * 100

    df['Report_Type'] = 'DISAGGREGATED'
    return df

# ─────────────────────────────────────────────────────────────────────────────
# 3. COMPUTE QUANT SIGNALS & ROLLING METRICS (VECTORIZED HIGH-SPEED)
# ─────────────────────────────────────────────────────────────────────────────
def compute_quant_features(df, window_1y=52, window_3y=156):
    """
    Computes COT Index (1Y, 3Y), Z-score (3Y), Flow Momentum, and Market Regime
    using vectorized pandas transforms for extreme speed.
    """
    df = df.sort_values(['Market', 'Date']).reset_index(drop=True)
    grp = df.groupby('Market')

    # Rolling min / max / mean / std
    min_1y = grp['Net_Spec'].transform(lambda s: s.rolling(window_1y, min_periods=max(5, window_1y//4)).min())
    max_1y = grp['Net_Spec'].transform(lambda s: s.rolling(window_1y, min_periods=max(5, window_1y//4)).max())
    r_1y = max_1y - min_1y
    cot_idx_1y = np.where(r_1y > 0, ((df['Net_Spec'] - min_1y) / r_1y) * 100, 50.0)

    min_3y = grp['Net_Spec'].transform(lambda s: s.rolling(window_3y, min_periods=max(10, window_3y//4)).min())
    max_3y = grp['Net_Spec'].transform(lambda s: s.rolling(window_3y, min_periods=max(10, window_3y//4)).max())
    r_3y = max_3y - min_3y
    cot_idx_3y = np.where(r_3y > 0, ((df['Net_Spec'] - min_3y) / r_3y) * 100, 50.0)

    mean_3y = grp['Net_Spec'].transform(lambda s: s.rolling(window_3y, min_periods=max(10, window_3y//4)).mean())
    std_3y  = grp['Net_Spec'].transform(lambda s: s.rolling(window_3y, min_periods=max(10, window_3y//4)).std())
    zscore_3y = np.where(std_3y > 0, (df['Net_Spec'] - mean_3y) / std_3y, 0.0)

    flow_1w = grp['Net_Spec'].diff(1)
    flow_4w = grp['Net_Spec'].diff(4)

    oi = df['Open_Interest_All']
    oi_shift1 = grp['Open_Interest_All'].shift(1)
    oi_pct_1w = ((oi - oi_shift1) / oi_shift1.replace(0, np.nan)) * 100

    new_cols = pd.DataFrame({
        'COT_Index_1Y': cot_idx_1y,
        'COT_Index_3Y': cot_idx_3y,
        'COT_ZScore_3Y': zscore_3y,
        'Flow_1W': flow_1w,
        'Flow_4W': flow_4w,
        'OI_Pct_1W': oi_pct_1w
    }, index=df.index)

    cond_extreme_long = (new_cols['COT_ZScore_3Y'] >= 1.8) | (new_cols['COT_Index_3Y'] >= 90)
    cond_extreme_short = (new_cols['COT_ZScore_3Y'] <= -1.8) | (new_cols['COT_Index_3Y'] <= 10)
    cond_acc = (new_cols['Flow_1W'] > 0) & (new_cols['Flow_4W'] > 0) & (new_cols['OI_Pct_1W'] > 0)
    cond_dist = (new_cols['Flow_1W'] < 0) & (new_cols['Flow_4W'] < 0) & (new_cols['OI_Pct_1W'] < 0)
    cond_inflow = (new_cols['Flow_1W'] > 0) & (new_cols['Flow_4W'] > 0)
    cond_outflow = (new_cols['Flow_1W'] < 0) & (new_cols['Flow_4W'] < 0)

    conditions = [cond_extreme_long, cond_extreme_short, cond_acc, cond_dist, cond_inflow, cond_outflow]
    choices = [
        '🔴 EXTREME LONG (Squeeze Risk)',
        '🟢 EXTREME SHORT (Short Squeeze Candidate)',
        '📈 STRONG ACCUMULATION (Trend Expansion)',
        '📉 STRONG DISTRIBUTION (Trend Exhaustion)',
        '↗ MILD INFLOW',
        '↘ MILD OUTFLOW'
    ]
    new_cols['Regime_Signal'] = np.select(conditions, choices, default='⚪ NEUTRAL')

    return pd.concat([df, new_cols], axis=1)

# ─────────────────────────────────────────────────────────────────────────────
# 4. LOOKAHEAD-SAFE DAILY RESAMPLER
# ─────────────────────────────────────────────────────────────────────────────
def generate_lookahead_safe_daily(df, start_date=None, end_date=None):
    """
    CFTC reports Tuesday data on Friday after 15:30 EST.
    Therefore, the first actionable trading day is next Monday (+6 days from Tuesday).
    This function shifts the availability date to Monday to prevent lookahead bias in quant strategies.
    """
    df = df.copy()
    # Shift Tuesday to Monday
    df['Actionable_Date'] = df['Date'] + pd.Timedelta(days=6)
    
    daily_records = []
    markets = df['Market'].unique()

    for m in markets:
        sub = df[df['Market'] == m].sort_values('Actionable_Date')
        if sub.empty:
            continue
        sub = sub.set_index('Actionable_Date')
        # Reindex to full calendar days and forward-fill
        d_idx = pd.date_range(start=sub.index.min(), end=sub.index.max(), freq='D')
        sub_daily = sub.reindex(d_idx).ffill()
        sub_daily['Market'] = m
        sub_daily['Trading_Date'] = sub_daily.index
        daily_records.append(sub_daily)

    if not daily_records:
        return pd.DataFrame()

    daily_df = pd.concat(daily_records, ignore_index=True)
    if start_date:
        daily_df = daily_df[daily_df['Trading_Date'] >= pd.to_datetime(start_date)]
    if end_date:
        daily_df = daily_df[daily_df['Trading_Date'] <= pd.to_datetime(end_date)]
    return daily_df
