"""
COT DATA RESEARCH LAB — SQLite Warehouse & Persistence Layer
Relational schema, indexing, and high-performance bulk upsert engine.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEPLOY_ROOT = os.path.dirname(CURRENT_DIR)
SQLITE_DIR = os.path.join(DEPLOY_ROOT, "data", "sqlite")
DB_PATH = os.path.join(SQLITE_DIR, "cot_warehouse.db")

os.makedirs(SQLITE_DIR, exist_ok=True)

def get_connection(timeout=30.0):
    """
    Returns a configured SQLite connection with WAL mode enabled for concurrent reads.
    """
    conn = sqlite3.connect(DB_PATH, timeout=timeout)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA cache_size=-64000;") # 64MB cache
    return conn

def init_database():
    """
    Initializes relational database schema with primary keys, constraints, and indexes.
    """
    conn = get_connection()
    cur = conn.cursor()

    # 1. Commodity Prices Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS commodity_prices (
        metal TEXT NOT NULL,
        date TEXT NOT NULL,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume REAL,
        daily_return REAL,
        volatility_20d REAL,
        price_trend REAL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (metal, date)
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_prices_metal_date ON commodity_prices (metal, date);")

    # 2. Macro Indicators Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS macro_indicators (
        series_id TEXT NOT NULL,
        date TEXT NOT NULL,
        value REAL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (series_id, date)
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_macro_series_date ON macro_indicators (series_id, date);")

    # 3. ICSG Canonical Fundamentals Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS icsg_fundamentals (
        metal TEXT NOT NULL,
        period_year INTEGER NOT NULL,
        metric TEXT NOT NULL,
        value_standardized REAL,
        unit_standardized TEXT,
        publication_date TEXT,
        available_at TEXT,
        source_id TEXT,
        is_forecast INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (metal, period_year, metric)
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_icsg_metal_year ON icsg_fundamentals (metal, period_year);")

    # 4. Pipeline Sync Metadata Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sync_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        records_upserted INTEGER DEFAULT 0,
        latest_data_date TEXT,
        status TEXT NOT NULL,
        message TEXT
    );
    """)

    conn.commit()
    conn.close()

def upsert_dataframe(df, table_name, conflict_keys, batch_size=5000):
    """
    Bulk upserts a Pandas DataFrame into target SQLite table using native
    INSERT INTO ... ON CONFLICT (...) DO UPDATE SET ...
    Handles schema synchronization by adding missing columns dynamically.
    """
    if df.empty:
        return 0

    df_clean = df.copy()
    
    # Standardize date columns to YYYY-MM-DD text format for SQLite
    for col in df_clean.columns:
        if pd.api.types.is_datetime64_any_dtype(df_clean[col]):
            df_clean[col] = df_clean[col].dt.strftime('%Y-%m-%d')

    conn = get_connection()
    cur = conn.cursor()

    # Check if table exists
    cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    table_exists = cur.fetchone() is not None

    if not table_exists:
        # Create table dynamically from dataframe
        # First ensure conflict keys are defined as PRIMARY KEY
        cols = list(df_clean.columns)
        col_defs = []
        for c in cols:
            dtype = df_clean[c].dtype
            if pd.api.types.is_integer_dtype(dtype):
                sql_type = "INTEGER"
            elif pd.api.types.is_float_dtype(dtype):
                sql_type = "REAL"
            else:
                sql_type = "TEXT"
            col_defs.append(f'"{c}" {sql_type}')
        
        pk_clause = f", PRIMARY KEY ({', '.join(['\"' + k + '\"' for k in conflict_keys])})"
        create_sql = f'CREATE TABLE "{table_name}" ({", ".join(col_defs)}{pk_clause});'
        cur.execute(create_sql)
        for k in conflict_keys:
            cur.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_{k}" ON "{table_name}" ("{k}");')
        conn.commit()
    else:
        # Check if table has missing columns and add them (Schema Evolution)
        cur.execute(f'PRAGMA table_info("{table_name}");')
        existing_cols = {row[1] for row in cur.fetchall()}
        for c in df_clean.columns:
            if c not in existing_cols:
                dtype = df_clean[c].dtype
                sql_type = "REAL" if pd.api.types.is_float_dtype(dtype) else "INTEGER" if pd.api.types.is_integer_dtype(dtype) else "TEXT"
                try:
                    cur.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "{c}" {sql_type};')
                except Exception:
                    pass
        conn.commit()

    # Fetch table columns in exact order
    cur.execute(f'PRAGMA table_info("{table_name}");')
    db_cols = [row[1] for row in cur.fetchall()]
    
    # Filter df to existing db cols
    common_cols = [c for c in df_clean.columns if c in db_cols]
    update_cols = [c for c in common_cols if c not in conflict_keys]

    cols_str = ', '.join([f'"{c}"' for c in common_cols])
    placeholders = ', '.join(['?' for _ in common_cols])
    conflict_str = ', '.join([f'"{k}"' for k in conflict_keys])
    
    if update_cols:
        update_clause = ', '.join([f'"{c}" = excluded."{c}"' for c in update_cols])
        sql = f'''
        INSERT INTO "{table_name}" ({cols_str})
        VALUES ({placeholders})
        ON CONFLICT ({conflict_str}) DO UPDATE SET {update_clause};
        '''
    else:
        sql = f'''
        INSERT OR IGNORE INTO "{table_name}" ({cols_str})
        VALUES ({placeholders});
        '''

    # Convert dataframe to tuples with NaN converted to None
    records = df_clean[common_cols].replace({np.nan: None}).to_dict(orient='split')['data']

    total_upserted = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        cur.executemany(sql, batch)
        total_upserted += len(batch)
        conn.commit()

    conn.close()
    return total_upserted

def query_dataframe(query, params=None):
    """
    Executes a SELECT query and returns results as a Pandas DataFrame.
    """
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()
    return df

def get_database_stats():
    """
    Returns summary statistics for the SQLite warehouse: table names, row counts, and disk usage.
    """
    if not os.path.exists(DB_PATH):
        return {"exists": False, "tables": {}, "size_mb": 0.0, "latest_syncs": []}

    size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cur.fetchall()]

    table_stats = {}
    for t in tables:
        cur.execute(f'SELECT COUNT(*) FROM "{t}";')
        cnt = cur.fetchone()[0]
        
        # Check min/max date if exists
        cur.execute(f'PRAGMA table_info("{t}");')
        col_names = [r[1] for r in cur.fetchall()]
        date_col = next((c for c in ['report_date', 'date', 'period_year'] if c in col_names), None)
        
        min_date, max_date = None, None
        if date_col:
            try:
                cur.execute(f'SELECT MIN("{date_col}"), MAX("{date_col}") FROM "{t}";')
                r = cur.fetchone()
                min_date, max_date = str(r[0]), str(r[1])
            except Exception:
                pass

        table_stats[t] = {
            "row_count": cnt,
            "min_date": min_date,
            "max_date": max_date
        }

    # Fetch recent sync events
    latest_syncs = []
    if "sync_metadata" in tables:
        cur.execute("SELECT source, sync_timestamp, records_upserted, latest_data_date, status, message FROM sync_metadata ORDER BY id DESC LIMIT 5;")
        for row in cur.fetchall():
            latest_syncs.append({
                "source": row[0],
                "timestamp": str(row[1]),
                "records": row[2],
                "latest_date": str(row[3]),
                "status": row[4],
                "message": row[5]
            })

    conn.close()
    return {
        "exists": True,
        "path": DB_PATH,
        "size_mb": round(size_mb, 2),
        "tables": table_stats,
        "latest_syncs": latest_syncs
    }

def record_sync_log(source, records_upserted, latest_data_date, status, message=""):
    """
    Appends an audit log entry into the sync_metadata table.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO sync_metadata (source, records_upserted, latest_data_date, status, message)
    VALUES (?, ?, ?, ?, ?);
    """, (source, records_upserted, str(latest_data_date), status, message))
    conn.commit()
    conn.close()
