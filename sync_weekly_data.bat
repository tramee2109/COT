@echo off
REM ==============================================================
REM COT Research Lab — Automated Weekly Data Sync Batch Runner
REM Target: Scheduled via Windows Task Scheduler every Saturday 06:00
REM ==============================================================
title COT Research Lab Weekly SQLite Sync
cd /d "%~dp0"

set PYTHON_EXEC=E:\My\the20\test_strategy\commodity_source\cot_analyze\.venv\Scripts\python.exe
if not exist "%PYTHON_EXEC%" (
    if exist "%~dp0.venv\Scripts\python.exe" (
        set PYTHON_EXEC=%~dp0.venv\Scripts\python.exe
    ) else (
        set PYTHON_EXEC=python
    )
)

echo [COT SYNC] Using Python: %PYTHON_EXEC%
echo [COT SYNC] Running Weekly Multi-Layer Pipeline Upsert...
"%PYTHON_EXEC%" sync_weekly_data.py

if %ERRORLEVEL% EQU 0 (
    echo [COT SYNC] Pipeline Sync Completed Successfully.
) else (
    echo [COT SYNC] Warning: Sync encountered errors or notices.
)
timeout /t 5
