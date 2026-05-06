@echo off
docker run --rm -v "%cd%\data:/app/data" mlb-roster-tracker
pause
