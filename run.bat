@echo off
echo Starting Library Project...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run server
python manage.py runserver

pause
