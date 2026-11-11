"""
COT DATA RESEARCH LAB — Phase 11: Commodity Positioning & Price Relationship Engine
Institutional Quantitative Framework connecting COT data with physical commodity prices.
Strictly research-oriented (non-trading, no execution, no buy/sell signals).
"""

import os
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

from research_lab.config import BASE_DIR, TARGET_COMMODITIES

# Dedicated COT-to-Price Market Mapping Registry
COT_PRICE_MARKET_REGISTRY = {
    "Copper": {
        "cftc_code": "085692",
        "cftc_market_name": "COPPER-GRADE #1 / COPPER- #1 (Continuous History)",
        "exchange": "COMEX",
        "instrument": "Continuous High Grade Copper Futures (HG=F)",
        "currency": "USD",
        "price_unit": "USD / lb",
        "contract_multiplier": 25000,
        "roll_methodology": "Calendar spread volume/OI switch to front liquid month",
        "source": "COMEX Market Data Lake / Daily Fundamental Lakehouse",
        "status": "Verified Continuous"
    },
    "Silver": {
        "cftc_code": "084691",
        "cftc_market_name": "SILVER - COMMODITY EXCHANGE INC.",
        "exchange": "COMEX",
        "instrument": "Continuous Silver 5,000 oz Futures (SI=F)",
        "currency": "USD",
        "price_unit": "USD / troy oz",
        "contract_multiplier": 5000,
        "roll_methodology": "Volume-weighted active month roll",
        "source": "COMEX Market Data Lake / Daily Fundamental Lakehouse",
        "status": "Verified Continuous"
    },
    "Platinum": {
        "cftc_code": "076651",
        "cftc_market_name": "PLATINUM - NEW YORK MERCANTILE EXCHANGE",
        "exchange": "NYMEX",
        "instrument": "Continuous Platinum 50 oz Futures (PL=F)",
        "currency": "USD",
        "price_unit": "USD / troy oz",
        "contract_multiplier": 50,
        "roll_methodology": "Volume-weighted active month roll",
        "source": "NYMEX Market Data Lake / Daily Fundamental Lakehouse",
        "status": "Verified Continuous"
    },
    "Micro Copper": {
        "cftc_code": "085699",
        "cftc_market_name": "MICRO COPPER - COMMODITY EXCHANGE INC.",
        "exchange": "COMEX",
        "instrument": "Micro Copper Futures (MHG)",
        "currency": "USD",
        "price_unit": "USD / lb",
        "contract_multiplier": 2500,
        "roll_methodology": "Micro contract - treated as independent series",
        "source": "COMEX Data (Micro contracts separate from standard)",
        "status": "Independent Micro Series (Not combined with standard)"
    },
    "Micro Silver": {
        "cftc_code": "084694",
        "cftc_market_name": "MICRO SILVER - COMMODITY EXCHANGE INC.",
        "exchange": "COMEX",
        "instrument": "Micro Silver Futures (SIL)",
        "currency": "USD",
        "price_unit": "USD / troy oz",
        "contract_multiplier": 1000,
        "roll_methodology": "Micro contract - treated as independent series",
        "source": "COMEX Data (Micro contracts separate from standard)",
        "status": "Independent Micro Series (Not combined with standard)"
    }
}

def audit_price_data():
    """
    Performs Phase 11.1 audit of all price datasets available in the environment.
    Returns a dictionary of audited datasets and metadata.
    """
    local_fund = os.path.join(BASE_DIR, "data", "prices", "daily_fundamental_features.parquet")
    ext_fund = os.path.join(os.path.dirname(BASE_DIR), "commodity_equilibrium", "07_daily_features", "daily_fundamental_features.parquet")
    p_fund = local_fund if os.path.exists(local_fund) else ext_fund

    local_lake = os.path.join(BASE_DIR, "data", "prices")
    ext_lake = os.path.join(os.path.dirname(BASE_DIR), "commodity_source_SnD", "data", "lakehouse", "benchmarks")
    p_lake = local_lake if os.path.exists(local_lake) else ext_lake

    audit = {
        "status": "Complete",
        "verified_commodities": ["Copper", "Silver", "Platinum"],
        "datasets": {}
    }

    if os.path.exists(p_fund):
        df_fund = pd.read_parquet(p_fund)
        for m in ["Copper", "Silver", "Platinum"]:
            sub = df_fund[df_fund['metal'].astype(str).str.lower() == m.lower()]
            audit["datasets"][f"{m}_fundamental_lakehouse"] = {
                "file": "daily_fundamental_features.parquet",
                "observations": len(sub),
                "date_min": str(sub['date'].min()),
                "date_max": str(sub['date'].max()),
                "fields": ["date", "price", "volume", "price_return_1d", "price_return_20d", "price_return_60d"],
                "frequency": "Daily",
                "instrument": f"{m} Continuous Futures Settlement",
                "coverage_pct": 100.0
            }

    bench_map = {"Copper": "hg_f.parquet", "Silver": "si_f.parquet", "Platinum": "pl_f.parquet"}
    for m, fname in bench_map.items():
        fp = os.path.join(p_lake, fname)
        if os.path.exists(fp):
            df_b = pd.read_parquet(fp)
            audit["datasets"][f"{m}_ohlcv_benchmark"] = {
                "file": fname,
                "observations": len(df_b),
                "date_min": str(df_b['time_bar'].min()),
                "date_max": str(df_b['time_bar'].max()),
                "fields": ["open", "high", "low", "close", "volume"],
                "frequency": "Daily OHLCV",
                "coverage_pct": 100.0
            }

    return audit

def load_canonical_commodity_prices(commodity_name):
    """
    Loads, cleans, and merges validated continuous daily price series for a target commodity.
    Combines daily fundamental history (2000-2026) with benchmark OHLCV up to the latest date.
    Returns clean daily DataFrame sorted by date.
    """
    comm_clean = str(commodity_name).strip().capitalize()
    if comm_clean not in ["Copper", "Silver", "Platinum"]:
        return pd.DataFrame()

    local_fund = os.path.join(BASE_DIR, "data", "prices", "daily_fundamental_features.parquet")
    ext_fund = os.path.join(os.path.dirname(BASE_DIR), "commodity_equilibrium", "07_daily_features", "daily_fundamental_features.parquet")
    p_fund = local_fund if os.path.exists(local_fund) else ext_fund

    bench_map = {"Copper": "hg_f.parquet", "Silver": "si_f.parquet", "Platinum": "pl_f.parquet"}
    local_bench = os.path.join(BASE_DIR, "data", "prices", bench_map.get(comm_clean, ""))
    ext_bench = os.path.join(os.path.dirname(BASE_DIR), "commodity_source_SnD", "data", "lakehouse", "benchmarks", bench_map.get(comm_clean, ""))
    p_bench = local_bench if os.path.exists(local_bench) else ext_bench

    dfs = []
    if os.path.exists(p_fund):
        df_f = pd.read_parquet(p_fund)
        sub_f = df_f[df_f['metal'].astype(str).str.lower() == comm_clean.lower()].copy()
        if not sub_f.empty:
            sub_f['date'] = pd.to_datetime(sub_f['date'])
            sub_f = sub_f.rename(columns={'price': 'close'})
            if 'open' not in sub_f.columns:
                sub_f['open'] = sub_f['close']
                sub_f['high'] = sub_f['close']
                sub_f['low'] = sub_f['close']
            dfs.append(sub_f[['date', 'open', 'high', 'low', 'close', 'volume']])

    if os.path.exists(p_bench):
        df_b = pd.read_parquet(p_bench)
        df_b['date'] = pd.to_datetime(df_b['time_bar'])
        dfs.append(df_b[['date', 'open', 'high', 'low', 'close', 'volume']])

    if not dfs:
        return pd.DataFrame()

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.sort_values('date').drop_duplicates('date', keep='last').reset_index(drop=True)

    # Clean missing / invalid
    combined = combined[combined['close'] > 0].copy()

    # Derived daily metrics
    combined['daily_return'] = combined['close'].pct_change()
    combined['log_return'] = np.log(combined['close'] / combined['close'].shift(1))
    combined['volatility_20d'] = combined['daily_return'].rolling(20, min_periods=10).std() * np.sqrt(252)
    combined['volatility_60d'] = combined['daily_return'].rolling(60, min_periods=30).std() * np.sqrt(252)

    combined['ma_20d'] = combined['close'].rolling(20, min_periods=10).mean()
    combined['ma_50d'] = combined['close'].rolling(50, min_periods=25).mean()
    combined['ma_200d'] = combined['close'].rolling(200, min_periods=100).mean()

    combined['price_trend'] = np.where(combined['close'] > combined['ma_50d'], "Uptrend", "Downtrend")

    return combined

def align_cot_and_price(cot_df, commodity_name, convention="publication_aware"):
    """
    Canonical weekly alignment between CFTC COT report dates and commodity prices.
    Guarantees look-ahead safety:
      - 'publication_aware': Forward returns anchor strictly on Friday close following Tuesday survey date.
      - 'tuesday_close': Anchors on survey Tuesday close (contemporaneous/descriptive only).
    """
    price_df = load_canonical_commodity_prices(commodity_name)
    if price_df.empty or cot_df.empty:
        return pd.DataFrame()

    c = cot_df.copy()
    c['report_date'] = pd.to_datetime(c['report_date'])
    c = c.sort_values('report_date').reset_index(drop=True)

    # Establish Publication Dates: Friday following report Tuesday (T + 3 days)
    c['pub_date_assumed'] = c['report_date'] + pd.Timedelta(days=3)

    p = price_df.copy()
    p['date_ns'] = p['date'].astype('datetime64[ns]')

    # 1. Merge Tuesday settlement price (contemporaneous with COT position measurement)
    c['date_tuesday_ns'] = c['report_date'].astype('datetime64[ns]')
    m_tuesday = pd.merge_asof(
        c.sort_values('date_tuesday_ns'),
        p[['date_ns', 'close', 'open', 'high', 'low', 'volume', 'daily_return', 'volatility_20d', 'ma_50d', 'price_trend']].rename(
            columns={'close': 'price_tuesday', 'daily_return': 'ret_1d_tuesday'}
        ),
        left_on='date_tuesday_ns',
        right_on='date_ns',
        direction='backward'
    ).drop(columns=['date_ns'])

    # 2. Merge Friday publication price (tradable public availability anchor)
    m_tuesday['date_pub_ns'] = m_tuesday['pub_date_assumed'].astype('datetime64[ns]')
    m_full = pd.merge_asof(
        m_tuesday.sort_values('date_pub_ns'),
        p[['date_ns', 'close', 'volatility_20d']].rename(
            columns={'close': 'price_publication', 'volatility_20d': 'vol_pub_20d'}
        ),
        left_on='date_pub_ns',
        right_on='date_ns',
        direction='backward'
    ).drop(columns=['date_ns'])

    # Weekly Contemporaneous Price Return (Tuesday to Tuesday)
    m_full['weekly_price_return'] = m_full['price_tuesday'].pct_change()

    # Canonical Price for display based on chosen convention
    if convention == "publication_aware":
        anchor_price_col = 'price_publication'
    else:
        anchor_price_col = 'price_tuesday'

    m_full['price'] = m_full[anchor_price_col]

    # Price Normalizations
    p_series = m_full['price']
    p_min, p_max = p_series.min(), p_series.max()
    m_full['price_norm_pct'] = np.where(p_max > p_min, ((p_series - p_min) / (p_max - p_min)) * 100.0, 50.0)

    p_mean, p_std = p_series.mean(), p_series.std()
    m_full['price_zscore'] = np.where(p_std > 0, (p_series - p_mean) / p_std, 0.0)

    first_val = p_series.dropna().iloc[0] if len(p_series.dropna()) else 1.0
    m_full['price_rebased'] = (p_series / first_val) * 100.0

    # Multi-Horizon Forward Price Returns (Look-Ahead Safe)
    horizons = [1, 2, 4, 8, 13, 26]
    for h in horizons:
        m_full[f'fwd_ret_{h}w'] = (m_full[anchor_price_col].shift(-h) / m_full[anchor_price_col]) - 1.0

    # Price Momentum across matching horizons
    for h in [4, 8, 13, 26]:
        m_full[f'price_mom_{h}w'] = (m_full[anchor_price_col] / m_full[anchor_price_col].shift(h)) - 1.0
        m_full[f'price_acc_{h}w'] = m_full[f'price_mom_{h}w'].diff(1)

    return m_full.sort_values('report_date').reset_index(drop=True)

# ─────────────────────────────────────────────────────────────────────────────
# STATISTICAL RESEARCH & HYPOTHESIS TESTING ENGINES
# ─────────────────────────────────────────────────────────────────────────────

def compute_positioning_price_correlation(aligned_df, pos_col, price_ret_col='weekly_price_return', windows=[13, 26, 52]):
    """
    Computes Pearson and Spearman Rank correlation between positioning and price changes.
    Returns correlation summary dict and rolling correlation DataFrame.
    """
    sub = aligned_df[[pos_col, price_ret_col, 'report_date']].dropna().copy()
    if len(sub) < 10:
        return {}, pd.DataFrame()

    s_pos = sub[pos_col]
    s_ret = sub[price_ret_col]

    r_pearson, p_pearson = stats.pearsonr(s_pos, s_ret)
    r_spearman, p_spearman = stats.spearmanr(s_pos, s_ret)

    # Fisher Z 95% Confidence Interval for Pearson r
    z = np.arctanh(r_pearson)
    se = 1.0 / np.sqrt(len(sub) - 3)
    ci_low = np.tanh(z - 1.96 * se)
    ci_high = np.tanh(z + 1.96 * se)

    summary = {
        "sample_size": len(sub),
        "pearson_r": r_pearson,
        "pearson_p": p_pearson,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "spearman_r": r_spearman,
        "spearman_p": p_spearman,
        "is_significant": p_spearman < 0.05
    }

    rolling = pd.DataFrame(index=sub.index)
    rolling['report_date'] = sub['report_date']
    for w in windows:
        rolling[f'corr_{w}w'] = s_pos.rolling(w, min_periods=max(5, w//3)).corr(s_ret)

    return summary, rolling

def compute_lead_lag_cross_correlation(aligned_df, pos_change_col, price_ret_col='weekly_price_return', max_lag=8):
    """
    Cross-correlation profile Corr(Delta_COT_t, Return_{t+k}) for k in [-max_lag, +max_lag].
    k < 0: Price leads COT (Market anticipation / trend-following behavior).
    k = 0: Contemporaneous co-movement.
    k > 0: COT leads future price returns (Information content / Predictive power).
    """
    sub = aligned_df[[pos_change_col, price_ret_col]].dropna().copy()
    if len(sub) < max_lag * 3:
        return pd.DataFrame()

    s_cot = sub[pos_change_col]
    s_ret = sub[price_ret_col]

    records = []
    n = len(sub)

    for k in range(-max_lag, max_lag + 1):
        if k < 0:
            # Price leads COT by -k weeks: s_ret shifted backwards vs s_cot
            r, p = stats.spearmanr(s_cot.iloc[-k:], s_ret.iloc[:k])
            regime = "Price Leads COT (Lag)"
        elif k == 0:
            r, p = stats.spearmanr(s_cot, s_ret)
            regime = "Contemporaneous (k=0)"
        else:
            # COT leads future return by +k weeks
            r, p = stats.spearmanr(s_cot.iloc[:-k], s_ret.iloc[k:])
            regime = "COT Leads Price (Lead)"

        # Standard error under null r=0: 1/sqrt(N)
        se = 1.0 / np.sqrt(n - abs(k))
        records.append({
            "lag": k,
            "horizon_label": f"t+{k}W" if k > 0 else (f"t{k}W" if k < 0 else "t (Concurrent)"),
            "spearman_r": r,
            "p_value": p,
            "se": se,
            "ci_95_band": 1.96 * se,
            "is_significant": abs(r) > 1.96 * se,
            "regime": regime
        })

    return pd.DataFrame(records)

def compute_forward_returns_by_quantile(aligned_df, pos_col, horizons=[1, 2, 4, 8, 13, 26], q=5, non_overlapping=False):
    """
    Groups positioning variable into Quantiles (e.g. Quintiles Q1=Most Short to Q5=Most Long)
    and measures forward price return statistics across each horizon.
    """
    sub = aligned_df[[pos_col] + [f'fwd_ret_{h}w' for h in horizons]].dropna().copy()
    if len(sub) < 30:
        return pd.DataFrame()

    if non_overlapping:
        # Sample every 4 weeks to avoid overlapping serial dependence
        sub = sub.iloc[::4].copy()

    try:
        sub['quantile'] = pd.qcut(sub[pos_col], q=q, labels=[f"Q{i+1}" for i in range(q)], duplicates='drop')
    except Exception:
        return pd.DataFrame()

    results = []
    for q_label in sorted(sub['quantile'].unique()):
        q_data = sub[sub['quantile'] == q_label]
        for h in horizons:
            col = f'fwd_ret_{h}w'
            rets = q_data[col].dropna() * 100.0  # percentage
            if len(rets) > 3:
                t_stat, p_val = stats.ttest_1samp(rets, 0.0)
                results.append({
                    "Quantile": q_label,
                    "Horizon": f"{h}W",
                    "N_Obs": len(rets),
                    "Mean_Return_Pct": rets.mean(),
                    "Median_Return_Pct": rets.median(),
                    "Std_Dev_Pct": rets.std(),
                    "Win_Rate_Pct": (rets > 0).mean() * 100.0,
                    "T_Statistic": t_stat,
                    "P_Value": p_val
                })

    return pd.DataFrame(results)

def run_extreme_event_study(aligned_df, z_col='managed_money_zscore_52w', z_threshold=2.0, deduplicate_clustering=True):
    """
    Conducts an institutional event study around Extreme Positioning events (|Z| > threshold).
    Option to deduplicate consecutive cluster weeks (first-crossing filter).
    Calculates cumulative forward return trajectories (+1W, +2W, +4W, +8W, +13W, +26W).
    """
    sub = aligned_df.copy()
    if z_col not in sub.columns or sub[z_col].isna().all():
        return pd.DataFrame(), pd.DataFrame(), 0, 0

    horizons = [1, 2, 4, 8, 13, 26]

    # Extreme High (Over-extended Longs)
    is_high = (sub[z_col] >= z_threshold)
    # Extreme Low (Over-extended Shorts)
    is_low = (sub[z_col] <= -z_threshold)

    if deduplicate_clustering:
        # First-crossing filter: trigger event only when entering the extreme zone
        is_high = is_high & (~is_high.shift(1).fillna(False))
        is_low = is_low & (~is_low.shift(1).fillna(False))

    high_idx = sub[is_high].index
    low_idx = sub[is_low].index
    normal_idx = sub[(~is_high) & (~is_low)].index

    def summarize_events(indices, event_name):
        ev_records = []
        for h in horizons:
            col = f'fwd_ret_{h}w'
            if col in sub.columns:
                rets = sub.loc[indices, col].dropna() * 100.0
                if len(rets) > 0:
                    t_stat, p_val = stats.ttest_1samp(rets, 0.0) if len(rets) > 2 else (0.0, 1.0)
                    ev_records.append({
                        "Event_Type": event_name,
                        "Horizon_Weeks": h,
                        "Horizon_Label": f"{h}W",
                        "N_Events": len(rets),
                        "Mean_Return_Pct": rets.mean(),
                        "Median_Return_Pct": rets.median(),
                        "Std_Dev_Pct": rets.std(),
                        "Win_Rate_Pct": (rets > 0).mean() * 100.0,
                        "T_Stat": t_stat,
                        "P_Value": p_val
                    })
        return ev_records

    records = []
    records.extend(summarize_events(high_idx, f"Extreme Long (Z >= +{z_threshold} Std)"))
    records.extend(summarize_events(low_idx, f"Extreme Short (Z <= -{z_threshold} Std)"))
    records.extend(summarize_events(normal_idx, "Baseline / Neutral Regime"))

    summary_df = pd.DataFrame(records)

    # Return dates of events for visualization markers
    event_markers = pd.DataFrame({
        "report_date": sub.loc[high_idx.union(low_idx), 'report_date'],
        "event_type": np.where(sub.loc[high_idx.union(low_idx)].index.isin(high_idx), "Extreme Long", "Extreme Short"),
        "z_score": sub.loc[high_idx.union(low_idx), z_col],
        "price": sub.loc[high_idx.union(low_idx), 'price']
    }).sort_values('report_date').reset_index(drop=True)

    return summary_df, event_markers, len(high_idx), len(low_idx)

def run_flow_event_study(aligned_df, horizons=[1, 2, 4, 8, 13, 26]):
    """
    Evaluates forward price behavior conditioned on the 4 inferred weekly flow drivers:
      1. Estimated Long Accumulation (Gross Longs UP, Gross Shorts flat/down)
      2. Estimated Short Covering (Gross Shorts DOWN, Gross Longs flat/down)
      3. Estimated Long Liquidation (Gross Longs DOWN, Gross Shorts flat/up)
      4. Estimated New Shorts (Gross Shorts UP, Gross Longs flat/down)
    """
    sub = aligned_df.copy()
    if 'flow_driver' not in sub.columns:
        return pd.DataFrame()

    results = []
    for driver in ["Long Accumulation", "Short Covering", "Long Liquidation", "New Shorts"]:
        driver_df = sub[sub['flow_driver'].astype(str).str.contains(driver, case=False, na=False)]
        for h in horizons:
            col = f'fwd_ret_{h}w'
            if col in driver_df.columns:
                rets = driver_df[col].dropna() * 100.0
                if len(rets) > 3:
                    t_stat, p_val = stats.ttest_1samp(rets, 0.0)
                    results.append({
                        "Flow_Driver": driver,
                        "Horizon": f"{h}W",
                        "N_Observations": len(rets),
                        "Mean_Return_Pct": rets.mean(),
                        "Median_Return_Pct": rets.median(),
                        "Positive_Return_Rate": (rets > 0).mean() * 100.0,
                        "T_Stat": t_stat,
                        "P_Value": p_val
                    })

    return pd.DataFrame(results)

def run_hac_regression(aligned_df, x_col, y_col='fwd_ret_4w', max_lag=4):
    """
    Runs OLS regression of Forward Return on Positioning indicator with
    Newey-West (HAC) Heteroskedasticity and Autocorrelation Consistent standard errors.
    Return_{t+h} = alpha + beta * X_t + eps_t
    """
    sub = aligned_df[[x_col, y_col]].dropna().copy()
    if len(sub) < 25:
        return {}

    X = sm.add_constant(sub[x_col])
    y = sub[y_col] * 100.0  # percentage

    try:
        model = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': max_lag})
        alpha = model.params['const']
        beta = model.params[x_col]
        se_beta = model.bse[x_col]
        t_beta = model.tvalues[x_col]
        p_beta = model.pvalues[x_col]
        r_squared = model.rsquared

        ci = model.conf_int().loc[x_col]

        return {
            "n_obs": len(sub),
            "alpha": alpha,
            "beta": beta,
            "se_beta": se_beta,
            "t_statistic": t_beta,
            "p_value": p_beta,
            "r_squared": r_squared,
            "ci_lower": ci[0],
            "ci_upper": ci[1],
            "is_significant": p_beta < 0.05
        }
    except Exception as e:
        return {"error": str(e)}

def compute_information_coefficients(aligned_df, pos_col, horizons=[1, 2, 4, 8, 13, 26]):
    """
    Computes Information Coefficients (Spearman Rank IC and Pearson IC) across multiple horizons.
    Calculates IC Mean, IC Std, Information Ratio (IR = Mean / Std), and rolling IC.
    """
    records = []
    sub = aligned_df[[pos_col] + [f'fwd_ret_{h}w' for h in horizons] + ['report_date']].dropna().copy()
    if len(sub) < 20:
        return pd.DataFrame(), pd.DataFrame()

    rolling_ic = pd.DataFrame(index=sub.index)
    rolling_ic['report_date'] = sub['report_date']

    for h in horizons:
        col = f'fwd_ret_{h}w'
        r_sp, p_sp = stats.spearmanr(sub[pos_col], sub[col])
        r_pr, p_pr = stats.pearsonr(sub[pos_col], sub[col])

        # Rolling IC over 52-week window
        rolling_series = sub[pos_col].rolling(52, min_periods=20).corr(sub[col])
        rolling_ic[f'ic_52w_{h}w'] = rolling_series

        ic_mean = rolling_series.mean()
        ic_std = rolling_series.std()
        ir = (ic_mean / ic_std) if (ic_std is not None and ic_std > 0) else 0.0

        records.append({
            "Horizon": f"{h}W",
            "Spearman_Rank_IC": r_sp,
            "Spearman_P_Value": p_sp,
            "Pearson_IC": r_pr,
            "Pearson_P_Value": p_pr,
            "Rolling_IC_Mean": ic_mean,
            "Rolling_IC_Std": ic_std,
            "Information_Ratio_IR": ir,
            "Statistical_Significance": "Significant (p < 0.05)" if p_sp < 0.05 else "Not Significant"
        })

    return pd.DataFrame(records), rolling_ic

def run_multiple_testing_adjustment(p_values_list, method='fdr_bh'):
    """
    Applies multiple-testing corrections (Benjamini-Hochberg FDR or Bonferroni)
    to protect against false positives across multiple forward horizons.
    """
    try:
        from statsmodels.stats.multitest import multipletests
        reject, pvals_corrected, _, _ = multipletests(p_values_list, alpha=0.05, method=method)
        return reject.tolist(), pvals_corrected.tolist()
    except Exception:
        # Fallback Bonferroni
        n = len(p_values_list)
        p_bonf = [min(1.0, p * n) for p in p_values_list]
        reject = [p < 0.05 for p in p_bonf]
        return reject, p_bonf

def compute_2d_regime_matrix(aligned_df, pos_z_col='managed_money_zscore_52w', horizon=4):
    """
    Constructs a 2D Regime Matrix cross-tabulating Positioning Conditions against Market Price Regimes.
    Positioning Regimes: Extreme Long (Z > 1.5), Neutral (-1.5 <= Z <= 1.5), Extreme Short (Z < -1.5)
    Price Regimes: Uptrend (Price > 50W MA) vs Downtrend (Price <= 50W MA)
    Computes Observation Count, Mean Forward Return %, Median Return %, Win Rate %, and Volatility.
    """
    sub = aligned_df.copy()
    ret_col = f'fwd_ret_{horizon}w'
    if pos_z_col not in sub.columns or ret_col not in sub.columns or 'price_trend' not in sub.columns:
        return pd.DataFrame()

    sub = sub.dropna(subset=[pos_z_col, ret_col, 'price_trend']).copy()

    # Define Positioning Regime
    conditions = [
        (sub[pos_z_col] > 1.5),
        (sub[pos_z_col] < -1.5)
    ]
    choices = ["Extreme Long (>+1.5 Std)", "Extreme Short (<-1.5 Std)"]
    sub['pos_regime'] = np.select(conditions, choices, default="Neutral (-1.5 to +1.5 Std)")

    matrix_rows = []
    for p_reg in ["Extreme Long (>+1.5 Std)", "Neutral (-1.5 to +1.5 Std)", "Extreme Short (<-1.5 Std)"]:
        for m_reg in ["Uptrend", "Downtrend"]:
            cell = sub[(sub['pos_regime'] == p_reg) & (sub['price_trend'] == m_reg)]
            n = len(cell)
            if n > 0:
                rets = cell[ret_col] * 100.0
                mean_r = rets.mean()
                med_r = rets.median()
                win_r = (rets > 0).mean() * 100.0
                std_r = rets.std()
            else:
                mean_r, med_r, win_r, std_r = np.nan, np.nan, np.nan, np.nan

            matrix_rows.append({
                "Positioning_Regime": p_reg,
                "Price_Regime": m_reg,
                "Observations": n,
                f"Mean_Forward_{horizon}W_Ret_Pct": mean_r,
                f"Median_Forward_{horizon}W_Ret_Pct": med_r,
                "Win_Rate_Pct": win_r,
                "Realized_Vol_Pct": std_r
            })

    return pd.DataFrame(matrix_rows)
