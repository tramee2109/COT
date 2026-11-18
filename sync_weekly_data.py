"""
COT DATA RESEARCH LAB — Standalone Weekly Sync & Upsert Runner
Can be scheduled via Windows Task Scheduler or executed from CLI:
    python sync_weekly_data.py
"""

import sys
import os

# Add root directory to path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from research_lab.data_sync import run_full_weekly_sync

if __name__ == "__main__":
    print("=" * 65)
    print("  COMMODITY RESEARCH LAB — WEEKLY SQLITE SYNC LAUNCHER")
    print("=" * 65)
    results = run_full_weekly_sync(verbose=True)
    print("\n✅ Sync run finished successfully.")
