@echo off
setlocal

cd /d C:\Users\testerjw\mlb-roster-tracker

REM If you use a virtual environment, activate it here:
REM call C:\Users\testerjw\mlb-roster-tracker\.venv\Scripts\activate.bat

python -m app.main

endlocal
