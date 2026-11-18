@echo off
REM ==============================================================
REM COT Research Lab — Automated Weekly Data Sync Batch Runner
REM Target: Scheduled via Windows Task Scheduler every Saturday 06:00
REM ==============================================================
title COT Research Lab Weekly SQLite Sync
cd /d "%~dp0"

echo [COT SYNC] Running Weekly Multi-Layer Pipeline Upsert...
python sync_weekly_data.py

if %ERRORLEVEL% EQU 0 (
    echo [COT SYNC] Pipeline Sync Completed Successfully.
) else (
    echo [COT SYNC] Warning: Sync encountered errors or notices.
)
timeout /t 5
