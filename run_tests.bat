@echo off
setlocal enabledelayedexpansion

echo ===================================
echo Running Library Tests
echo ===================================

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo Running tests with custom test runner...
python manage.py test library

echo.
echo If you encounter any issues, try running specific test files:
echo python manage.py test library.tests.test_models
echo python manage.py test library.tests.test_views_basic
echo.

pause
