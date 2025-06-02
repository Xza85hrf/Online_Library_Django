@echo off
setlocal enabledelayedexpansion

echo ===================================
echo Installing Core Requirements
echo ===================================

REM Check if virtual environment exists and is activated
if not defined VIRTUAL_ENV (
    echo Virtual environment not activated.
    echo Please run 'venv\Scripts\activate.bat' first.
    pause
    exit /b 1
)

echo Installing Django...
pip install Django>=4.2,<5.0

echo Installing Pillow for image processing...
pip install Pillow>=9.0.0

echo Installing django-filter...
pip install django-filter>=22.1

echo Installing django-crispy-forms...
pip install django-crispy-forms>=2.0

echo Installing djangorestframework...
pip install djangorestframework>=3.13.0

echo.
echo ===================================
echo Core installation complete!
echo ===================================
echo.
echo You can now run the project with: run_library.bat
echo.

pause
