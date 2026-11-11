"""
GLOBAL COMMODITY INTELLIGENCE PLATFORM — Copper Fundamental & Macro Data Access Service
Modular, publication-aware, zero-lookahead service for Copper physical fundamentals and FRED macro data.
Strictly analytical and non-trading.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEPLOY_ROOT = os.path.dirname(CURRENT_DIR)

MACRO_DIR = os.path.join(DEPLOY_ROOT, "data", "macro")
FUNDAMENTALS_DIR = os.path.join(DEPLOY_ROOT, "data", "fundamentals")
CANONICAL_PARQUET = os.path.join(FUNDAMENTALS_DIR, "fundamental_latest.parquet")

def load_canonical_fundamentals(metal="Copper"):
    """
    Loads verified canonical fundamental supply-demand observations (ICSG / WPIC / Silver Inst / USGS).
    Preserves exact publication dates, observation periods, units, and forecast flags.
    """
    if not os.path.exists(CANONICAL_PARQUET):
        # Fallback to adjacent directory if not yet copied
        alt_path = r"E:\My\the20\test_strategy\commodity_source\commodity_equilibrium\06_canonical\fundamental_latest.parquet"
        if os.path.exists(alt_path):
            df = pd.read_parquet(alt_path)
        else:
            return pd.DataFrame()
    else:
        df = pd.read_parquet(CANONICAL_PARQUET)

    if metal and "metal" in df.columns:
        df = df[df["metal"] == metal].copy()

    # Ensure date typing
    if "publication_date" in df.columns:
        df["publication_date"] = pd.to_datetime(df["publication_date"])
    if "available_at" in df.columns:
        df["available_at"] = pd.to_datetime(df["available_at"])

    return df.sort_values(["period_year", "metric"])

def load_fred_macro_series():
    """
    Loads daily official FRED macro factor series:
    - DFII10: US 10-Year Real Yield (%)
    - DGS10: US 10-Year Nominal Yield (%)
    - T10YIE: US 10-Year Breakeven Inflation Rate (%)
    - DTWEXBGS: Nominal Broad U.S. Dollar Index (NOT ICE DXY)
    """
    series_map = {
        "DFII10": ("macro__fred__us_10y_real_yield__DFII10__daily.csv", "us_10y_real_yield"),
        "DGS10": ("macro__fred__us_10y_nominal_yield__DGS10__daily.csv", "us_10y_nominal_yield"),
        "T10YIE": ("macro__fred__us_10y_breakeven_inflation__T10YIE__daily.csv", "us_10y_breakeven_inflation"),
        "DTWEXBGS": ("macro__fred__trade_weighted_usd_broad__DTWEXBGS__daily.csv", "nominal_broad_usd_index")
    }

    merged_df = None

    for code, (fname, clean_col) in series_map.items():
        fpath = os.path.join(MACRO_DIR, fname)
        if not os.path.exists(fpath):
            alt_fpath = os.path.join(r"E:\My\the20\test_strategy\commodity_source\commodity_equilibrium\02_raw\macro_cross", fname)
            if os.path.exists(alt_fpath):
                fpath = alt_fpath
            else:
                continue

        df_s = pd.read_csv(fpath)
        date_col = [c for c in df_s.columns if "date" in c.lower()][0]
        val_col = [c for c in df_s.columns if c != date_col][0]

        df_s["date"] = pd.to_datetime(df_s[date_col])
        df_s[clean_col] = pd.to_numeric(df_s[val_col], errors="coerce")
        df_s = df_s[["date", clean_col]].dropna(subset=["date"]).sort_values("date")

        if merged_df is None:
            merged_df = df_s
        else:
            merged_df = pd.merge(merged_df, df_s, on="date", how="outer")

    if merged_df is not None:
        merged_df = merged_df.sort_values("date").reset_index(drop=True)
    else:
        merged_df = pd.DataFrame()

    return merged_df

def align_copper_price_cot_macro_fundamentals(market_df, price_df, convention="publication_aware"):
    """
    Constructs an aligned, zero-lookahead, multi-layer research panel for Copper.
    Layers:
    1. Copper COMEX Continuous Settlement Price & Returns
    2. CFTC Disaggregated Speculative & Commercial Positioning
    3. FRED Real Yields & Nominal Broad USD Index
    4. ICSG Supply-Demand Fundamentals (Strictly respecting available_at publication lag)
    """
    from research_lab.price_engine import align_cot_and_price

    # 1. Base Price + COT alignment
    aligned_base = align_cot_and_price(market_df, "Copper", convention=convention)
    if aligned_base.empty:
        return pd.DataFrame()

    aligned_base["report_date"] = pd.to_datetime(aligned_base["report_date"])
    aligned_base = aligned_base.sort_values("report_date").reset_index(drop=True)

    # 2. Merge Macro Series
    macro_df = load_fred_macro_series()
    if not macro_df.empty:
        macro_df["date"] = pd.to_datetime(macro_df["date"])
        
        # In publication-aware mode, anchor to Friday close (same as COT publication)
        # Use merge_asof backward to ensure zero lookahead
        aligned_base = pd.merge_asof(
            aligned_base,
            macro_df,
            left_on="report_date",
            right_on="date",
            direction="backward"
        )
        if "date" in aligned_base.columns:
            aligned_base = aligned_base.drop(columns=["date"])

    # 3. Attach ICSG Fundamentals with Strict Publication Lag
    canon_fund = load_canonical_fundamentals(metal="Copper")
    if not canon_fund.empty and "available_at" in canon_fund.columns:
        # Pivot annual canonical metrics by publication release date
        # Available metrics: mine_production, refined_production, refined_usage
        fund_piv = canon_fund.pivot_table(
            index="available_at",
            columns="metric",
            values="value_standardized",
            aggfunc="last"
        ).reset_index()

        fund_piv["available_at"] = pd.to_datetime(fund_piv["available_at"])
        if "refined_production" in fund_piv.columns and "refined_usage" in fund_piv.columns:
            fund_piv["icsg_apparent_balance_kt"] = fund_piv["refined_production"] - fund_piv["refined_usage"]

        # Rename columns to avoid collision
        fund_piv = fund_piv.rename(columns={
            "mine_production": "icsg_mine_production_kt",
            "refined_production": "icsg_refined_production_kt",
            "refined_usage": "icsg_refined_usage_kt"
        })

        # Merge asof backward: A fundamental release is ONLY known on or after its available_at date
        aligned_base = pd.merge_asof(
            aligned_base,
            fund_piv,
            left_on="report_date",
            right_on="available_at",
            direction="backward"
        )

    return aligned_base

