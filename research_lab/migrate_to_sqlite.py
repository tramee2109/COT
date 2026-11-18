"""
COT DATA RESEARCH LAB — Historical Data Migration to SQLite Warehouse
Ingests existing Parquet and CSV files into the SQLite database.
"""

import os
import sys
import time
import pandas as pd
import numpy as np

# Add project root to sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEPLOY_ROOT = os.path.dirname(CURRENT_DIR)
if DEPLOY_ROOT not in sys.path:
    sys.path.insert(0, DEPLOY_ROOT)

from research_lab.database import (
    init_database,
    upsert_dataframe,
    record_sync_log,
    get_database_stats
)
from research_lab.config import (
    DATA_DISAGG_PATH,
    DATA_TFF_PATH,
    PRICES_PARQUET_PATH
)

DATA_DISAGG_PQ = DATA_DISAGG_PATH.replace(".csv", ".parquet")
DATA_TFF_PQ = DATA_TFF_PATH.replace(".csv", ".parquet")
MACRO_DIR = os.path.join(DEPLOY_ROOT, "data", "macro")
FUNDAMENTALS_PARQUET = os.path.join(DEPLOY_ROOT, "data", "fundamentals", "fundamental_latest.parquet")

def migrate_all_historical_data(verbose=True):
    """
    Executes complete migration of all available historical datasets into SQLite.
    Returns migration summary dict.
    """
    start_time = time.time()
    if verbose:
        print("🚀 Initializing SQLite Relational Warehouse Schema...")
    init_database()

    summary = {}

    # 1. Migrate Disaggregated COT
    if verbose:
        print("\n📦 [1/5] Migrating Disaggregated COT Dataset...")
    if os.path.exists(DATA_DISAGG_PQ):
        df_disagg = pd.read_parquet(DATA_DISAGG_PQ)
    elif os.path.exists(DATA_DISAGG_PATH):
        df_disagg = pd.read_csv(DATA_DISAGG_PATH, low_memory=False)
    else:
        df_disagg = pd.DataFrame()

    if not df_disagg.empty:
        # Standardize keys
        df_disagg['report_date'] = pd.to_datetime(df_disagg['Report_Date_as_YYYY-MM-DD'], errors='coerce')
        df_disagg = df_disagg.dropna(subset=['report_date'])
        df_disagg['report_date'] = df_disagg['report_date'].dt.strftime('%Y-%m-%d')
        df_disagg['contract_code_clean'] = df_disagg['CFTC_Contract_Market_Code'].astype(str).str.strip().str.zfill(6)
        df_disagg['market_name_clean'] = df_disagg['Market_and_Exchange_Names'].astype(str).str.strip()
        df_disagg['report_family'] = 'Disaggregated COT'

        n_disagg = upsert_dataframe(
            df_disagg,
            table_name="cot_disaggregated",
            conflict_keys=["contract_code_clean", "report_date"]
        )
        latest_date = df_disagg['report_date'].max()
        record_sync_log("Migration_Disaggregated_COT", n_disagg, latest_date, "SUCCESS", f"Initial migration of {n_disagg} records")
        summary["cot_disaggregated"] = n_disagg
        if verbose:
            print(f"✅ Upserted {n_disagg:,} Disaggregated COT records (Max date: {latest_date})")

    # 2. Migrate Traders in Financial Futures (TFF)
    if verbose:
        print("\n📦 [2/5] Migrating Traders in Financial Futures (TFF)...")
    if os.path.exists(DATA_TFF_PQ):
        df_tff = pd.read_parquet(DATA_TFF_PQ)
    elif os.path.exists(DATA_TFF_PATH):
        df_tff = pd.read_csv(DATA_TFF_PATH, low_memory=False)
    else:
        df_tff = pd.DataFrame()

    if not df_tff.empty:
        t_d1 = pd.to_datetime(df_tff['Report_Date_as_YYYY-MM-DD'], errors='coerce') if 'Report_Date_as_YYYY-MM-DD' in df_tff.columns else pd.Series()
        t_d2 = pd.to_datetime(df_tff['Report_Date_as_MM_DD_YYYY'], errors='coerce') if 'Report_Date_as_MM_DD_YYYY' in df_tff.columns else pd.Series()
        df_tff['report_date'] = t_d1.combine_first(t_d2)
        df_tff = df_tff.dropna(subset=['report_date'])
        df_tff['report_date'] = df_tff['report_date'].dt.strftime('%Y-%m-%d')
        df_tff['contract_code_clean'] = df_tff['CFTC_Contract_Market_Code'].astype(str).str.strip().str.zfill(6)
        df_tff['market_name_clean'] = df_tff['Market_and_Exchange_Names'].astype(str).str.strip()
        df_tff['report_family'] = 'Traders in Financial Futures (TFF)'

        n_tff = upsert_dataframe(
            df_tff,
            table_name="cot_tff",
            conflict_keys=["contract_code_clean", "report_date"]
        )
        latest_date = df_tff['report_date'].max()
        record_sync_log("Migration_TFF_COT", n_tff, latest_date, "SUCCESS", f"Initial migration of {n_tff} records")
        summary["cot_tff"] = n_tff
        if verbose:
            print(f"✅ Upserted {n_tff:,} TFF COT records (Max date: {latest_date})")

    # 3. Migrate Verified Commodity Settlement Prices
    if verbose:
        print("\n📦 [3/5] Migrating Commodity Prices Lakehouse...")
    if os.path.exists(PRICES_PARQUET_PATH):
        df_prices = pd.read_parquet(PRICES_PARQUET_PATH)
        if not df_prices.empty and "date" in df_prices.columns:
            df_prices['date'] = pd.to_datetime(df_prices['date']).dt.strftime('%Y-%m-%d')
            # Ensure metal field exists
            if 'metal' not in df_prices.columns:
                df_prices['metal'] = 'Copper'

            # Standardize column naming
            rename_map = {'price': 'close'}
            df_prices = df_prices.rename(columns=rename_map)

            cols_to_keep = ['metal', 'date', 'open', 'high', 'low', 'close', 'volume', 'daily_return', 'volatility_20d', 'price_trend']
            existing_cols = [c for c in cols_to_keep if c in df_prices.columns]
            
            n_prices = upsert_dataframe(
                df_prices[existing_cols],
                table_name="commodity_prices",
                conflict_keys=["metal", "date"]
            )
            latest_date = df_prices['date'].max()
            record_sync_log("Migration_Commodity_Prices", n_prices, latest_date, "SUCCESS", f"Initial migration of {n_prices} price bars")
            summary["commodity_prices"] = n_prices
            if verbose:
                print(f"✅ Upserted {n_prices:,} Commodity Price records (Max date: {latest_date})")

    # 4. Migrate FRED Macro Indicators
    if verbose:
        print("\n📦 [4/5] Migrating FRED Macro Factors...")
    series_map = {
        "DFII10": ("macro__fred__us_10y_real_yield__DFII10__daily.csv", "US 10Y Real Yield"),
        "DGS10": ("macro__fred__us_10y_nominal_yield__DGS10__daily.csv", "US 10Y Nominal Yield"),
        "T10YIE": ("macro__fred__us_10y_breakeven_inflation__T10YIE__daily.csv", "US 10Y Breakeven Inflation"),
        "DTWEXBGS": ("macro__fred__trade_weighted_usd_broad__DTWEXBGS__daily.csv", "Nominal Broad USD Index")
    }

    total_macro = 0
    for sid, (fname, sname) in series_map.items():
        fpath = os.path.join(MACRO_DIR, fname)
        if os.path.exists(fpath):
            df_s = pd.read_csv(fpath)
            d_col = [c for c in df_s.columns if "date" in c.lower()][0]
            v_col = [c for c in df_s.columns if c != d_col][0]
            
            df_s['date'] = pd.to_datetime(df_s[d_col], errors='coerce')
            df_s = df_s.dropna(subset=['date'])
            df_s['date'] = df_s['date'].dt.strftime('%Y-%m-%d')
            df_s['value'] = pd.to_numeric(df_s[v_col], errors='coerce')
            df_s['series_id'] = sid
            
            clean_sub = df_s[['series_id', 'date', 'value']].dropna(subset=['value'])
            n_s = upsert_dataframe(
                clean_sub,
                table_name="macro_indicators",
                conflict_keys=["series_id", "date"]
            )
            total_macro += n_s

    record_sync_log("Migration_FRED_Macro", total_macro, "Various", "SUCCESS", f"Initial migration of {total_macro} daily macro records")
    summary["macro_indicators"] = total_macro
    if verbose:
        print(f"✅ Upserted {total_macro:,} FRED Macro indicator records across 4 series")

    # 5. Migrate ICSG Canonical Fundamentals
    if verbose:
        print("\n📦 [5/5] Migrating ICSG Canonical Fundamentals...")
    if os.path.exists(FUNDAMENTALS_PARQUET):
        df_fund = pd.read_parquet(FUNDAMENTALS_PARQUET)
        if not df_fund.empty:
            if 'publication_date' in df_fund.columns:
                df_fund['publication_date'] = pd.to_datetime(df_fund['publication_date']).dt.strftime('%Y-%m-%d')
            if 'available_at' in df_fund.columns:
                df_fund['available_at'] = pd.to_datetime(df_fund['available_at']).dt.strftime('%Y-%m-%d')
            
            # Map columns
            keep_cols = ['metal', 'period_year', 'metric', 'value_standardized', 'unit_standardized', 'publication_date', 'available_at', 'source_id', 'is_forecast']
            valid_cols = [c for c in keep_cols if c in df_fund.columns]
            
            n_fund = upsert_dataframe(
                df_fund[valid_cols],
                table_name="icsg_fundamentals",
                conflict_keys=["metal", "period_year", "metric"]
            )
            record_sync_log("Migration_ICSG_Fundamentals", n_fund, str(df_fund['period_year'].max()), "SUCCESS", f"Initial migration of {n_fund} fundamental records")
            summary["icsg_fundamentals"] = n_fund
            if verbose:
                print(f"✅ Upserted {n_fund:,} ICSG Canonical Fundamental records")

    elapsed = round(time.time() - start_time, 2)
    if verbose:
        print(f"\n🎉 Historical Data Migration Completed in {elapsed}s!")
        stats = get_database_stats()
        print(f"Database Size: {stats['size_mb']} MB at {stats['path']}")
        for t, s in stats['tables'].items():
            print(f"  • {t}: {s['row_count']:,} rows (Range: {s['min_date']} to {s['max_date']})")

    return summary

if __name__ == "__main__":
    migrate_all_historical_data(verbose=True)
