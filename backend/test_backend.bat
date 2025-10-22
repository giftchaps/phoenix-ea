@echo off
echo Phoenix EA Backend Test Suite
echo =============================

REM Check if we're in the right directory
if not exist "src\api\main.py" (
    echo Error: Please run this script from the backend directory
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Run tests
echo Running backend tests...
python run_tests.py

REM Keep window open
pause
