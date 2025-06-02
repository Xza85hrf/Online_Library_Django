@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting Django development server...
python manage.py runserver

REM Keep the window open if there's an error
if %ERRORLEVEL% neq 0 (
    echo An error occurred while running the server.
    pause
)
