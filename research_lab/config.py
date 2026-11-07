"""
COT DATA RESEARCH LAB — Configuration & Institutional Styling
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DISAGG_PATH = os.path.join(BASE_DIR, "data_disaggregated", "cot_disagg_full.csv")
DATA_TFF_PATH = os.path.join(BASE_DIR, "data", "cot_full_2010_2026.csv")
LOCAL_PRICES_PATH = os.path.join(BASE_DIR, "data", "prices", "daily_fundamental_features.parquet")
EXTERNAL_PRICES_PATH = os.path.join(
    os.path.dirname(BASE_DIR),
    "commodity_equilibrium",
    "07_daily_features",
    "daily_fundamental_features.parquet"
)
PRICES_PARQUET_PATH = LOCAL_PRICES_PATH if os.path.exists(LOCAL_PRICES_PATH) else EXTERNAL_PRICES_PATH

# Target Commodity Verified Codes
TARGET_COMMODITIES = {
    "Copper": {
        "code": "085692",
        "exchange": "COMEX",
        "names": [
            "COPPER-GRADE #1 - COMMODITY EXCHANGE INC.",
            "COPPER- #1 - COMMODITY EXCHANGE INC."
        ],
        "name_transition_date": "2022-02-08",
        "description": "High Grade Copper Futures (COMEX)"
    },
    "Silver": {
        "code": "084691",
        "exchange": "COMEX",
        "names": ["SILVER - COMMODITY EXCHANGE INC."],
        "description": "Silver 5,000 Troy Oz Futures (COMEX)"
    },
    "Platinum": {
        "code": "076651",
        "exchange": "NYMEX",
        "names": ["PLATINUM - NEW YORK MERCANTILE EXCHANGE"],
        "description": "Platinum 50 Troy Oz Futures (NYMEX)"
    },
    "Micro Copper": {
        "code": "085699",
        "exchange": "COMEX",
        "names": ["MICRO COPPER - COMMODITY EXCHANGE INC."],
        "description": "Micro Copper Futures (Separate Market)"
    },
    "Micro Silver": {
        "code": "084694",
        "exchange": "COMEX",
        "names": ["MICRO SILVER - COMMODITY EXCHANGE INC."],
        "description": "Micro Silver Futures (Separate Market)"
    }
}

# Institutional Color Palette
COLORS = {
    # Core Position Colors
    "long": "#2ecc71",           # Emerald Green
    "short": "#e74c3c",          # Coral Red
    "net": "#00d2d3",            # Cyan
    "open_interest": "#8395a7",  # Neutral Slate Gray
    "spread": "#feca57",         # Amber Yellow
    
    # Disaggregated COT Trader Categories
    "prod_merc": "#3867d6",      # Royal Blue
    "swap_dealer": "#fa8231",    # Safety Orange
    "managed_money": "#8854d0",  # Vivid Purple
    "other_rept": "#20bf6b",     # Teal
    "non_rept": "#778ca3",       # Ash Gray
    
    # TFF COT Trader Categories
    "dealer": "#2e86de",         # Blue
    "asset_mgr": "#f1c40f",      # Gold
    "lev_money": "#e056fd",      # Magenta
    "tff_other": "#10ac84",      # Dark Teal
    "tff_non_rept": "#95a5a6",   # Muted Gray
    
    # UI Dark Theme Styling
    "bg_dark": "#0e1117",
    "card_bg": "#181d27",
    "card_border": "#283142",
    "text_primary": "#f1f2f6",
    "text_muted": "#a4b0be",
    "accent": "#4bcffa"
}

# Standard Lookback Windows for Normalization
DEFAULT_LOOKBACK_WEEKS = 156   # 3 Years
LOOKBACK_OPTIONS = [52, 104, 156, 208, 260]

# Forward Return Horizons for Research
FORWARD_HORIZONS = [1, 2, 4, 8, 13]

