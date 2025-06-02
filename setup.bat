@echo off
echo Setting up Library Project...

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

echo Setup complete
echo.
echo To run the project:
echo 1. Activate the virtual environment: venv\Scripts\activate.bat
echo 2. Run the server: python manage.py runserver

pause
