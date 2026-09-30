@echo off
echo ⚡ Launching OpsMind AI Incident Response Agent...
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe run.py
) else (
    python run.py
)
pause
