"""
COT DATA RESEARCH LAB — Quantitative Positioning Metrics & Decomposition Engine
"""

import numpy as np
import pandas as pd

def safe_div(a, b, fill_val=0.0):
    """Safe division explicitly handling zero, null and infinite denominators."""
    with np.errstate(divide='ignore', invalid='ignore'):
        c = np.true_divide(a, b)
        c[~np.isfinite(c)] = fill_val
    return c

def compute_trader_metrics(df, report_family="Disaggregated COT"):
    """
    Computes canonical trader metrics, Net Positions, OI ratios, and Long/Short ratios
    strictly preserving report family category separation.
    """
    d = df.copy()
    oi = d['Open_Interest_All'].replace(0, np.nan)

    if "Disaggregated" in report_family:
        # Producer / Merchant
        d['prod_merc_net'] = d['Prod_Merc_Positions_Long_All'] - d['Prod_Merc_Positions_Short_All']
        d['prod_merc_net_pct_oi'] = safe_div(d['prod_merc_net'], oi) * 100.0
        d['prod_merc_long_pct_oi'] = safe_div(d['Prod_Merc_Positions_Long_All'], oi) * 100.0
        d['prod_merc_short_pct_oi'] = safe_div(d['Prod_Merc_Positions_Short_All'], oi) * 100.0
        d['prod_merc_ls_ratio'] = safe_div(d['Prod_Merc_Positions_Long_All'], d['Prod_Merc_Positions_Short_All'].replace(0, np.nan))

        # Swap Dealers
        # Handle typo in official CFTC CSV: 'Swap__Positions_Short_All'
        swap_short_col = 'Swap__Positions_Short_All' if 'Swap__Positions_Short_All' in d.columns else 'Swap_Positions_Short_All'
        d['swap_net'] = d['Swap_Positions_Long_All'] - d[swap_short_col]
        d['swap_net_pct_oi'] = safe_div(d['swap_net'], oi) * 100.0
        d['swap_spread_pct_oi'] = safe_div(d.get('Swap__Positions_Spread_All', 0), oi) * 100.0

        # Managed Money (Primary Speculative Category)
        d['managed_money_net'] = d['M_Money_Positions_Long_All'] - d['M_Money_Positions_Short_All']
        d['managed_money_net_pct_oi'] = safe_div(d['managed_money_net'], oi) * 100.0
        d['managed_money_long_pct_oi'] = safe_div(d['M_Money_Positions_Long_All'], oi) * 100.0
        d['managed_money_short_pct_oi'] = safe_div(d['M_Money_Positions_Short_All'], oi) * 100.0
        d['managed_money_ls_ratio'] = safe_div(d['M_Money_Positions_Long_All'], d['M_Money_Positions_Short_All'].replace(0, np.nan))
        
        # Spreading treated separately
        d['managed_money_spread_pct_oi'] = safe_div(d['M_Money_Positions_Spread_All'], oi) * 100.0

        # Other Reportables & Nonreportable
        d['other_rept_net'] = d['Other_Rept_Positions_Long_All'] - d['Other_Rept_Positions_Short_All']
        d['other_rept_net_pct_oi'] = safe_div(d['other_rept_net'], oi) * 100.0

        d['non_rept_net'] = d['NonRept_Positions_Long_All'] - d['NonRept_Positions_Short_All']
        d['non_rept_net_pct_oi'] = safe_div(d['non_rept_net'], oi) * 100.0

        # Canonical Primary Speculative Series for Analysis
        d['primary_spec_net'] = d['managed_money_net']
        d['primary_commercial_net'] = d['prod_merc_net']

    else:
        # TFF COT
        d['dealer_net'] = d['Dealer_Positions_Long_All'] - d['Dealer_Positions_Short_All']
        d['dealer_net_pct_oi'] = safe_div(d['dealer_net'], oi) * 100.0

        d['asset_mgr_net'] = d['Asset_Mgr_Positions_Long_All'] - d['Asset_Mgr_Positions_Short_All']
        d['asset_mgr_net_pct_oi'] = safe_div(d['asset_mgr_net'], oi) * 100.0

        d['lev_money_net'] = d['Lev_Money_Positions_Long_All'] - d['Lev_Money_Positions_Short_All']
        d['lev_money_net_pct_oi'] = safe_div(d['lev_money_net'], oi) * 100.0
        d['lev_money_ls_ratio'] = safe_div(d['Lev_Money_Positions_Long_All'], d['Lev_Money_Positions_Short_All'].replace(0, np.nan))
        d['lev_money_spread_pct_oi'] = safe_div(d['Lev_Money_Positions_Spread_All'], oi) * 100.0

        d['other_rept_net'] = d['Other_Rept_Positions_Long_All'] - d['Other_Rept_Positions_Short_All']
        d['non_rept_net'] = d['NonRept_Positions_Long_All'] - d['NonRept_Positions_Short_All']

        # Canonical Primary Speculative Series for Financials
        d['primary_spec_net'] = d['lev_money_net']
        d['primary_commercial_net'] = d['dealer_net']

    return d

def compute_position_decomposition(df, category_prefix="M_Money"):
    """
    Decomposes changes in Net Position into:
    - Long Accumulation (new longs)
    - Short Covering (shorts closed)
    - Long Liquidation (longs closed)
    - New Short Formation (new shorts opened)
    """
    d = df.copy()
    long_col = f"{category_prefix}_Positions_Long_All"
    short_col = f"{category_prefix}_Positions_Short_All"

    if long_col not in d.columns or short_col not in d.columns:
        return d

    d['delta_long'] = d[long_col].diff(1)
    d['delta_short'] = d[short_col].diff(1)
    d['delta_net'] = d['delta_long'] - d['delta_short']

    # Decomposition
    d['decomp_long_acc'] = np.where(d['delta_long'] > 0, d['delta_long'], 0)
    d['decomp_short_cov'] = np.where(d['delta_short'] < 0, -d['delta_short'], 0)
    d['decomp_long_liq'] = np.where(d['delta_long'] < 0, d['delta_long'], 0)
    d['decomp_new_short'] = np.where(d['delta_short'] > 0, -d['delta_short'], 0)

    return d

def compute_rolling_momentum(df, series_col="primary_spec_net", windows=[4, 8, 13, 26]):
    """
    Calculates rolling positioning momentum and acceleration over specified weeks.
    """
    d = df.copy()
    for w in windows:
        mom_col = f"momentum_{w}w"
        d[mom_col] = d[series_col].diff(w)
        # Acceleration is change in rolling momentum
        d[f"accel_{w}w"] = d[mom_col].diff(1)
    return d

def compute_historical_extremes(df, series_col="primary_spec_net", lookback_window=156):
    """
    Computes rolling percentile and rolling Z-score strictly avoiding lookahead bias
    (using rolling window with minimum period requirement).
    Computes for both 52-week (1-year) and 156-week (3-year) windows.
    """
    d = df.copy()
    s = d[series_col]
    
    windows = list(set([52, lookback_window]))
    for w in windows:
        min_p = max(10, w // 4)
        r_min = s.rolling(w, min_periods=min_p).min()
        r_max = s.rolling(w, min_periods=min_p).max()
        r_range = r_max - r_min

        d[f"percentile_{w}w"] = np.where(r_range > 0, ((s - r_min) / r_range) * 100.0, 50.0)

        r_mean = s.rolling(w, min_periods=min_p).mean()
        r_std = s.rolling(w, min_periods=min_p).std()
        d[f"zscore_{w}w"] = np.where(r_std > 0, (s - r_mean) / r_std, 0.0)

    return d

def compute_positioning_divergence(df, report_family="Disaggregated COT"):
    """
    Computes positioning divergence spread between Speculative Capital and Commercial Hedgers:
    - In Disaggregated: Managed Money Net % OI minus Producer/Merchant Net % OI
    - In TFF: Leveraged Money Net % OI minus Dealer Net % OI
    Also calculates rolling Z-scores of this divergence spread.
    """
    d = df.copy()
    if "Disaggregated" in report_family:
        if 'managed_money_net_pct_oi' in d.columns and 'prod_merc_net_pct_oi' in d.columns:
            d['divergence_spread'] = d['managed_money_net_pct_oi'] - d['prod_merc_net_pct_oi']
            d['divergence_label'] = "Managed Money vs Producer/Merchant Spread (% OI)"
        else:
            d['divergence_spread'] = np.nan
            d['divergence_label'] = "N/A"
    else:
        if 'lev_money_net_pct_oi' in d.columns and 'dealer_net_pct_oi' in d.columns:
            d['divergence_spread'] = d['lev_money_net_pct_oi'] - d['dealer_net_pct_oi']
            d['divergence_label'] = "Leveraged Money vs Dealer Spread (% OI)"
        else:
            d['divergence_spread'] = np.nan
            d['divergence_label'] = "N/A"

    if 'divergence_spread' in d.columns and not d['divergence_spread'].isna().all():
        s = d['divergence_spread']
        for w in [52, 156]:
            m = s.rolling(w, min_periods=max(10, w//4)).mean()
            std = s.rolling(w, min_periods=max(10, w//4)).std()
            d[f'divergence_zscore_{w}w'] = np.where(std > 0, (s - m) / std, 0.0)

    return d

def compute_rolling_pair_correlation(df, col1, col2, windows=[13, 26, 52], use_changes=False):
    """
    Computes rolling correlation between two columns across multiple windows (13W, 26W, 52W).
    Can calculate on levels or weekly changes (Δ).
    """
    d = df.copy()
    s1 = d[col1].diff(1) if use_changes else d[col1]
    s2 = d[col2].diff(1) if use_changes else d[col2]

    res = pd.DataFrame(index=d.index)
    res['report_date'] = d['report_date']

    for w in windows:
        min_p = max(5, w // 3)
        res[f'corr_{w}w'] = s1.rolling(w, min_periods=min_p).corr(s2)

    return res

def align_price_with_cot(cot_df, price_df, commodity_name):
    """
    Matches physical settlement prices with COT reporting dates.
    Calculates raw, normalized (0-100), Z-score, and rebased (100) price series.
    """
    if price_df.empty or cot_df.empty:
        return pd.DataFrame()

    p_sub = price_df[price_df['metal'].astype(str).str.lower() == str(commodity_name).lower()].copy()
    if p_sub.empty:
        return pd.DataFrame()

    p_sub['date_ns'] = pd.to_datetime(p_sub['date']).astype('datetime64[ns]')
    p_sub = p_sub.sort_values('date_ns').drop_duplicates('date_ns')

    c_sub = cot_df.copy()
    c_sub['date_ns'] = pd.to_datetime(c_sub['report_date']).astype('datetime64[ns]')
    c_sub = c_sub.sort_values('date_ns')

    merged = pd.merge_asof(c_sub, p_sub[['date_ns', 'price', 'volume']], on='date_ns', direction='nearest')

    # Add normalized versions
    p = merged['price']
    p_min, p_max = p.min(), p.max()
    merged['price_norm_pct'] = np.where(p_max > p_min, ((p - p_min) / (p_max - p_min)) * 100.0, 50.0)

    p_mean, p_std = p.mean(), p.std()
    merged['price_zscore'] = np.where(p_std > 0, (p - p_mean) / p_std, 0.0)

    first_val = p.dropna().iloc[0] if len(p.dropna()) else 1.0
    merged['price_rebased'] = (p / first_val) * 100.0

    return merged

