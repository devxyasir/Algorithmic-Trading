@echo off
cls
echo ============================================================================
echo    TRADING ANALYZER - 52+ Indicators
echo    Real-Time Entry/Exit/Stop Detection
echo ============================================================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

echo [OK] Python found
echo.

@REM REM Install dependencies
@REM echo Installing dependencies...
@REM pip install -q pandas numpy yfinance ta eel PyYAML

@REM if %errorlevel% neq 0 (
@REM     echo [ERROR] Failed to install dependencies
@REM     pause
@REM     exit /b 1
@REM )

@REM echo [OK] Dependencies installed
@REM echo.

REM Start application
echo Starting dashboard...
echo.
echo Dashboard will open at: http://localhost:8080
echo.
echo Press Ctrl+C to stop
echo ============================================================================
echo.

python app.py

pause
