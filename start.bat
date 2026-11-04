@echo off
rem Double-click to start GymAI. Pass -Setup to reinstall dependencies.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
pause
