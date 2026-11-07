"""
COT DATA RESEARCH LAB — Statistical Research Engine
"""

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller, acf, pacf

def compute_descriptive_stats(series, name="Series"):
    """
    Computes rigorous descriptive statistics for a financial positioning series.
    """
    s = pd.Series(series).dropna()
    if len(s) < 3:
        return {}

    mean_val = s.mean()
    median_val = s.median()
    std_val = s.std()
    min_val = s.min()
    max_val = s.max()
    skew_val = stats.skew(s)
    kurt_val = stats.kurtosis(s) # excess kurtosis
    q25 = np.percentile(s, 25)
    q75 = np.percentile(s, 75)
    iqr = q75 - q25

    return {
        "Metric": name,
        "Observations": len(s),
        "Mean": mean_val,
        "Median": median_val,
        "Std Dev": std_val,
        "Min": min_val,
        "Max": max_val,
        "Skewness": skew_val,
        "Excess Kurtosis": kurt_val,
        "IQR": iqr,
        "25th Pct": q25,
        "75th Pct": q75
    }

def perform_stationarity_test(series):
    """
    Performs Augmented Dickey-Fuller (ADF) stationarity test.
    Returns test statistic, p-value, critical values, and interpretation.
    """
    s = pd.Series(series).dropna()
    if len(s) < 20:
        return {"error": "Insufficient sample size for ADF test (N < 20)"}

    try:
        result = adfuller(s, autolag='AIC')
        return {
            "adf_statistic": result[0],
            "p_value": result[1],
            "used_lags": result[2],
            "n_obs": result[3],
            "crit_1pct": result[4]['1%'],
            "crit_5pct": result[4]['5%'],
            "crit_10pct": result[4]['10%'],
            "is_stationary_5pct": result[1] < 0.05,
            "conclusion": "Stationary (Reject Unit Root, p < 0.05)" if result[1] < 0.05 else "Non-Stationary (Unit Root Present, p >= 0.05)"
        }
    except Exception as e:
        return {"error": str(e)}

def compute_autocorrelations(series, nlags=12):
    """
    Computes Autocorrelation (ACF) and Partial Autocorrelation (PACF) values.
    """
    s = pd.Series(series).dropna()
    if len(s) <= nlags:
        nlags = max(1, len(s) // 3)

    try:
        acf_vals = acf(s, nlags=nlags, fft=True)
        pacf_vals = pacf(s, nlags=nlags, method='ols')
        lags = list(range(len(acf_vals)))
        return pd.DataFrame({
            "Lag": lags,
            "ACF": acf_vals,
            "PACF": pacf_vals
        })
    except Exception as e:
        return pd.DataFrame()

def compute_trader_correlation_matrix(df, report_family="Disaggregated COT", use_changes=False):
    """
    Computes correlation matrix between trader categories.
    If use_changes=True, correlates weekly changes (Δ) to avoid spurious level trends.
    """
    d = df.copy()
    if "Disaggregated" in report_family:
        cols = {
            "Prod / Merc": "prod_merc_net",
            "Swap Dealers": "swap_net",
            "Managed Money": "managed_money_net",
            "Other Rept": "other_rept_net",
            "Nonreportable": "non_rept_net"
        }
    else:
        cols = {
            "Dealer": "dealer_net",
            "Asset Manager": "asset_mgr_net",
            "Leveraged Money": "lev_money_net",
            "Other Rept": "other_rept_net",
            "Nonreportable": "non_rept_net"
        }

    valid_cols = {k: v for k, v in cols.items() if v in d.columns}
    sub = d[list(valid_cols.values())].rename(columns={v: k for k, v in valid_cols.items()})

    if use_changes:
        sub = sub.diff(1).dropna()
    else:
        sub = sub.dropna()

    return sub.corr()

def compute_cross_commodity_comparison(df_all, target_codes=["085692", "084691", "076651"], metric="managed_money_net_pct_oi"):
    """
    Extracts and standardizes positioning across Copper, Silver, and Platinum
    to allow direct cross-commodity comparison without scale distortion.
    """
    records = []
    code_names = {
        "085692": "Copper (COMEX)",
        "084691": "Silver (COMEX)",
        "076651": "Platinum (NYMEX)"
    }

    for code, label in code_names.items():
        sub = df_all[df_all['contract_code_clean'] == code].sort_values('report_date').copy()
        if not sub.empty and metric in sub.columns:
            s = sub[['report_date', metric]].copy()
            s['Commodity'] = label
            records.append(s)

    if not records:
        return pd.DataFrame()

    comb = pd.concat(records, ignore_index=True)
    pivot = comb.pivot(index='report_date', columns='Commodity', values=metric)
    return pivot.sort_index()

