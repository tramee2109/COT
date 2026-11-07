"""
COT DATA RESEARCH LAB — Empirical Information Content & Event Study Engine
"""

import numpy as np
import pandas as pd
from scipy import stats

def merge_cot_with_prices(cot_df, price_df, commodity_name="Copper"):
    """
    Merges weekly COT data with physical daily price settlement data.
    Enforces lookahead-safe alignment:
    - COT report_date is Tuesday.
    - Public release occurs Friday at 15:30 EST.
    - Actionable evaluation price begins on next Monday (report_date + 6 days).
    """
    if price_df.empty or cot_df.empty:
        return pd.DataFrame()

    p_sub = price_df[price_df['metal'].astype(str).str.lower() == commodity_name.lower()].copy()
    if p_sub.empty:
        return pd.DataFrame()

    p_sub['date'] = pd.to_datetime(p_sub['date'])
    p_sub = p_sub.sort_values('date').set_index('date')

    # Forward returns from actionable date (Monday)
    # 1W = 5 trading days, 2W = 10 days, 4W = 20 days, 8W = 40 days, 13W = 65 days
    horizons = {
        "fwd_ret_1w": 5,
        "fwd_ret_2w": 10,
        "fwd_ret_4w": 20,
        "fwd_ret_8w": 40,
        "fwd_ret_13w": 65
    }

    c = cot_df.copy()
    c['actionable_date'] = c['report_date'] + pd.Timedelta(days=6)
    
    records = []
    price_dates = p_sub.index

    for _, row in c.iterrows():
        act_d = row['actionable_date']
        # Find closest trading day on or after actionable Monday
        valid_idx = price_dates[price_dates >= act_d]
        if len(valid_idx) == 0:
            continue
        base_d = valid_idx[0]
        base_price = p_sub.loc[base_d, 'price']
        
        row_dict = row.to_dict()
        row_dict['base_eval_date'] = base_d
        row_dict['base_price'] = base_price

        # Calculate forward returns
        base_pos = price_dates.get_loc(base_d)
        for h_name, h_days in horizons.items():
            target_pos = base_pos + h_days
            if target_pos < len(price_dates):
                fwd_price = p_sub.iloc[target_pos]['price']
                row_dict[h_name] = ((fwd_price - base_price) / base_price) * 100.0
            else:
                row_dict[h_name] = np.nan
                
        records.append(row_dict)

    return pd.DataFrame(records)

def compute_information_coefficient(merged_df, positioning_col="managed_money_net_pct_oi", horizon_col="fwd_ret_4w"):
    """
    Computes Spearman rank Information Coefficient (IC) between positioning and forward price return.
    """
    sub = merged_df[[positioning_col, horizon_col]].dropna()
    if len(sub) < 15:
        return {"error": "Insufficient observations (N < 15)"}

    spearman_corr, p_value = stats.spearmanr(sub[positioning_col], sub[horizon_col])
    pearson_corr, p_val_p = stats.pearsonr(sub[positioning_col], sub[horizon_col])

    return {
        "n_obs": len(sub),
        "spearman_ic": spearman_corr,
        "spearman_pvalue": p_value,
        "pearson_corr": pearson_corr,
        "pearson_pvalue": p_val_p,
        "is_significant_5pct": p_value < 0.05
    }

def run_extreme_positioning_event_study(merged_df, positioning_col="managed_money_net_pct_oi", high_pct=90, low_pct=10):
    """
    Empirical event study:
    Analyzes forward return distributions when positioning reaches top decile (>90th percentile)
    versus bottom decile (<10th percentile).
    """
    sub = merged_df.copy()
    if positioning_col not in sub.columns or len(sub) < 30:
        return {}

    p_series = sub[positioning_col].dropna()
    threshold_high = np.percentile(p_series, high_pct)
    threshold_low = np.percentile(p_series, low_pct)

    events_high = sub[sub[positioning_col] >= threshold_high]
    events_low = sub[sub[positioning_col] <= threshold_low]
    events_normal = sub[(sub[positioning_col] > threshold_low) & (sub[positioning_col] < threshold_high)]

    horizons = ["fwd_ret_1w", "fwd_ret_2w", "fwd_ret_4w", "fwd_ret_8w", "fwd_ret_13w"]
    results = []

    for h in horizons:
        if h not in sub.columns:
            continue
        h_high = events_high[h].dropna()
        h_low = events_low[h].dropna()
        h_norm = events_normal[h].dropna()

        # Two-sample t-test (High vs Low)
        t_stat, p_val = stats.ttest_ind(h_high, h_low, equal_var=False) if len(h_high) > 3 and len(h_low) > 3 else (np.nan, np.nan)

        results.append({
            "Horizon": h.replace("fwd_ret_", "").upper(),
            "High_N": len(h_high),
            "High_Mean_Ret": h_high.mean() if len(h_high) else np.nan,
            "High_Median_Ret": h_high.median() if len(h_high) else np.nan,
            "High_WinRate": (h_high > 0).mean() * 100.0 if len(h_high) else np.nan,
            "Low_N": len(h_low),
            "Low_Mean_Ret": h_low.mean() if len(h_low) else np.nan,
            "Low_Median_Ret": h_low.median() if len(h_low) else np.nan,
            "Low_WinRate": (h_low > 0).mean() * 100.0 if len(h_low) else np.nan,
            "T_Statistic": t_stat,
            "P_Value": p_val
        })

    return pd.DataFrame(results), threshold_high, threshold_low

