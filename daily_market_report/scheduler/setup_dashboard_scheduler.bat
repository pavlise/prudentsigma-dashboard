@echo off
REM Setup Windows Task Scheduler for Streamlit Dashboard using schtasks
setlocal enabledelayedexpansion

set TASK_NAME=PrudentSigma Dashboard
set SCRIPT_PATH="C:\Users\Pavlos Elpidorou\Documents\AI_Project\daily_market_report\scheduler\start_dashboard.bat"
set WORKING_DIR=C:\Users\Pavlos Elpidorou\Documents\AI_Project

REM Delete existing task if it exists
schtasks /delete /tn "%TASK_NAME%" /f 2>nul

REM Create new scheduled task
schtasks /create /tn "%TASK_NAME%" /tr %SCRIPT_PATH% /sc daily /st 05:55 /rl highest

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Dashboard scheduled successfully!
    echo.
    echo Schedule:
    echo  - Runs daily at 5:55 AM
    echo  - Available at: http://localhost:8501
    echo  - Network URL: http://192.168.10.15:8501
    echo.
    echo Reports:
    echo  - Generated daily at 6:00 AM
    echo.
) else (
    echo Error creating scheduled task. Exit code: %ERRORLEVEL%
)

endlocal
