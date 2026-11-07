@echo off
REM COT Data Research Lab Start Script for Windows

SET SCRIPT_DIR=%~dp0
CD /D "%SCRIPT_DIR%"

IF NOT EXIST ".venv" (
    echo .venv not found. Creating virtual environment...
    python -m venv .venv
    IF %ERRORLEVEL% NEQ 0 (
        echo Error: Failed to create virtual environment.
        pause
        exit /b 1
    )
    
    echo Installing requirements...
    call .venv\Scripts\activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt scipy statsmodels
    IF %ERRORLEVEL% NEQ 0 (
        echo Error: Failed to install requirements.
        pause
        exit /b 1
    )
) ELSE (
    call .venv\Scripts\activate
)

echo ==============================================================================
echo Launching COT Data Research Lab (Institutional Quantitative Workstation)...
echo ==============================================================================
echo URL (Local): http://localhost:8501
echo URL (Network): http://192.168.1.19:8501
call .venv\Scripts\activate
python -m streamlit run run_research_lab.py --server.address 0.0.0.0
pause
