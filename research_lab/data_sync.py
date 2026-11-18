"""
COT DATA RESEARCH LAB — Automated Weekly Data Fetcher & SQLite Upsert Engine
Downloads latest weekly CFTC COT reports, daily commodity settlement prices, and FRED macro factors,
then atomically upserts them into the SQLite warehouse.
"""

import os
import sys
import time
import io
import zipfile
import urllib.request
import datetime
import pandas as pd
import numpy as np

# Add project root to sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEPLOY_ROOT = os.path.dirname(CURRENT_DIR)
if DEPLOY_ROOT not in sys.path:
    sys.path.insert(0, DEPLOY_ROOT)

from research_lab.database import (
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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def sync_cftc_cot(year=None, verbose=True):
    """
    Fetches the latest official CFTC weekly report for the target year (defaults to current year)
    and upserts into SQLite tables: cot_disaggregated and cot_tff.
    """
    if year is None:
        year = datetime.datetime.now().year

    sync_results = {}

    # 1. Fetch Disaggregated COT (Futures & Options Combined)
    disagg_url = f"https://www.cftc.gov/files/dea/history/com_disagg_txt_{year}.zip"
    if verbose:
        print(f"📥 [CFTC Disaggregated] Downloading {disagg_url}...")

    try:
        req = urllib.request.Request(disagg_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as response:
            zip_bytes = response.read()

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            txt_filenames = [n for n in z.namelist() if n.endswith(('.txt', '.csv'))]
            if not txt_filenames:
                raise ValueError("No text or CSV file found inside CFTC zip archive")
            target_txt = txt_filenames[0]
            if verbose:
                print(f"  ↳ Extracting {target_txt}...")
            with z.open(target_txt) as f:
                df_disagg = pd.read_csv(f, low_memory=False)

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
        record_sync_log("CFTC_Disaggregated_Weekly", n_disagg, latest_date, "SUCCESS", f"Upserted {n_disagg} records from {year}")
        sync_results["cot_disaggregated"] = {"records": n_disagg, "latest_date": latest_date, "status": "SUCCESS"}
        if verbose:
            print(f"✅ [CFTC Disaggregated] Upserted {n_disagg:,} records (Latest date: {latest_date})")

    except Exception as e:
        err_msg = str(e)
        if verbose:
            print(f"⚠️ [CFTC Disaggregated] Download notice: {err_msg}")
        record_sync_log("CFTC_Disaggregated_Weekly", 0, "N/A", "FAILED", err_msg)
        sync_results["cot_disaggregated"] = {"records": 0, "status": "FAILED", "error": err_msg}

    # 2. Fetch Traders in Financial Futures (TFF Combined)
    tff_url = f"https://www.cftc.gov/files/dea/history/com_fin_txt_{year}.zip"
    if verbose:
        print(f"📥 [CFTC TFF] Downloading {tff_url}...")

    try:
        req = urllib.request.Request(tff_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as response:
            zip_bytes = response.read()

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            txt_filenames = [n for n in z.namelist() if n.endswith(('.txt', '.csv'))]
            if not txt_filenames:
                raise ValueError("No text or CSV file found inside CFTC zip archive")
            target_txt = txt_filenames[0]
            if verbose:
                print(f"  ↳ Extracting {target_txt}...")
            with z.open(target_txt) as f:
                df_tff = pd.read_csv(f, low_memory=False)

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
        record_sync_log("CFTC_TFF_Weekly", n_tff, latest_date, "SUCCESS", f"Upserted {n_tff} records from {year}")
        sync_results["cot_tff"] = {"records": n_tff, "latest_date": latest_date, "status": "SUCCESS"}
        if verbose:
            print(f"✅ [CFTC TFF] Upserted {n_tff:,} records (Latest date: {latest_date})")

    except Exception as e:
        err_msg = str(e)
        if verbose:
            print(f"⚠️ [CFTC TFF] Download notice: {err_msg}")
        record_sync_log("CFTC_TFF_Weekly", 0, "N/A", "FAILED", err_msg)
        sync_results["cot_tff"] = {"records": 0, "status": "FAILED", "error": err_msg}

    return sync_results

def sync_commodity_prices(metals=["Copper", "Silver", "Platinum"], verbose=True):
    """
    Fetches continuous futures daily OHLCV prices from Yahoo Finance and upserts into SQLite.
    Computes lookahead-safe daily returns, 20-day volatility, and 50-day moving average trend.
    """
    import yfinance as yf

    symbol_map = {
        "Copper": "HG=F",
        "Silver": "SI=F",
        "Platinum": "PL=F"
    }

    sync_results = {}
    total_upserted = 0

    for metal in metals:
        ticker = symbol_map.get(metal)
        if not ticker:
            continue

        if verbose:
            print(f"📈 [Price Sync] Fetching {metal} ({ticker}) from Yahoo Finance...")

        try:
            # Fetch last 90 days of daily data for fast incremental upsert
            df_p = yf.download(ticker, period="3mo", interval="1d", progress=False, auto_adjust=True)
            if df_p.empty:
                continue

            # Flatten multi-index columns if present
            if isinstance(df_p.columns, pd.MultiIndex):
                df_p.columns = df_p.columns.get_level_values(0)

            df_p = df_p.reset_index()
            # Standardize column names
            df_p.columns = [c.lower() for c in df_p.columns]
            date_col = next((c for c in ['date', 'datetime'] if c in df_p.columns), 'date')
            df_p['date'] = pd.to_datetime(df_p[date_col]).dt.strftime('%Y-%m-%d')
            df_p['metal'] = metal

            # Calculate derived technical factors
            df_p['daily_return'] = df_p['close'].pct_change()
            df_p['volatility_20d'] = df_p['daily_return'].rolling(20).std()
            ma_50 = df_p['close'].rolling(50).mean()
            df_p['price_trend'] = np.where(df_p['close'] > ma_50, 1.0, np.where(df_p['close'] < ma_50, -1.0, 0.0))

            cols_to_keep = ['metal', 'date', 'open', 'high', 'low', 'close', 'volume', 'daily_return', 'volatility_20d', 'price_trend']
            valid_cols = [c for c in cols_to_keep if c in df_p.columns]

            n_p = upsert_dataframe(
                df_p[valid_cols],
                table_name="commodity_prices",
                conflict_keys=["metal", "date"]
            )
            latest_date = df_p['date'].max()
            total_upserted += n_p
            sync_results[metal] = {"records": n_p, "latest_date": latest_date, "status": "SUCCESS"}
            if verbose:
                print(f"✅ [Price Sync] {metal}: Upserted {n_p} bars (Latest date: {latest_date})")

        except Exception as e:
            err_msg = str(e)
            if verbose:
                print(f"⚠️ [Price Sync] Error for {metal}: {err_msg}")
            sync_results[metal] = {"records": 0, "status": "FAILED", "error": err_msg}

    record_sync_log("YahooFinance_Prices", total_upserted, "Various", "SUCCESS" if total_upserted > 0 else "PARTIAL", f"Upserted {total_upserted} price bars")
    return sync_results

def sync_fred_macro(verbose=True):
    """
    Downloads the latest daily macro factors directly from St. Louis Fed (FRED) CSV endpoints
    and upserts into SQLite macro_indicators table.
    """
    series_map = {
        "DFII10": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10",
        "DTWEXBGS": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTWEXBGS",
        "DGS10": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10",
        "T10YIE": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=T10YIE"
    }

    sync_results = {}
    total_upserted = 0

    for sid, url in series_map.items():
        if verbose:
            print(f"💵 [FRED Macro] Fetching {sid} from {url}...")
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                csv_bytes = resp.read()

            df_s = pd.read_csv(io.BytesIO(csv_bytes))
            d_col = [c for c in df_s.columns if "date" in c.lower()][0]
            v_col = [c for c in df_s.columns if c != d_col][0]

            df_s['date'] = pd.to_datetime(df_s[d_col], errors='coerce')
            df_s = df_s.dropna(subset=['date'])
            df_s['date'] = df_s['date'].dt.strftime('%Y-%m-%d')
            df_s['value'] = pd.to_numeric(df_s[v_col], errors='coerce')
            df_s['series_id'] = sid

            clean_df = df_s[['series_id', 'date', 'value']].dropna(subset=['value'])
            
            # Upsert into SQLite
            n_m = upsert_dataframe(
                clean_df,
                table_name="macro_indicators",
                conflict_keys=["series_id", "date"]
            )
            latest_date = clean_df['date'].max()
            total_upserted += n_m
            sync_results[sid] = {"records": n_m, "latest_date": latest_date, "status": "SUCCESS"}
            if verbose:
                print(f"✅ [FRED Macro] {sid}: Upserted {n_m} daily observations (Latest date: {latest_date})")

        except Exception as e:
            err_msg = str(e)
            if verbose:
                print(f"⚠️ [FRED Macro] Error for {sid}: {err_msg}")
            sync_results[sid] = {"records": 0, "status": "FAILED", "error": err_msg}

    record_sync_log("FRED_Macro_Direct", total_upserted, "Various", "SUCCESS" if total_upserted > 0 else "PARTIAL", f"Upserted {total_upserted} macro values")
    return sync_results

def run_full_weekly_sync(verbose=True):
    """
    Executes full multi-asset pipeline sync:
    1. CFTC COT Weekly (Disaggregated + TFF)
    2. Commodity Daily Prices (Copper, Silver, Platinum)
    3. FRED Macro Series (DFII10, DTWEXBGS, DGS10, T10YIE)
    """
    t0 = time.time()
    if verbose:
        print("=" * 70)
        print("🚀 STARTING WEEKLY MULTI-LAYER DATA PIPELINE SYNC")
        print("=" * 70)

    cot_res = sync_cftc_cot(verbose=verbose)
    price_res = sync_commodity_prices(verbose=verbose)
    macro_res = sync_fred_macro(verbose=verbose)

    elapsed = round(time.time() - t0, 2)
    stats = get_database_stats()

    if verbose:
        print("=" * 70)
        print(f"🎉 PIPELINE SYNC COMPLETED IN {elapsed}s!")
        print(f"Database Current Size: {stats['size_mb']} MB")
        for tbl, s in stats['tables'].items():
            print(f"  • {tbl}: {s['row_count']:,} rows (Max date: {s['max_date']})")
        print("=" * 70)

    return {
        "cot": cot_res,
        "prices": price_res,
        "macro": macro_res,
        "elapsed_seconds": elapsed,
        "database_stats": stats
    }

if __name__ == "__main__":
    run_full_weekly_sync(verbose=True)
