import subprocess
import sys
import time
import os
from pathlib import Path

# Locate root directory
ROOT_DIR = Path(__file__).resolve().parent
ENV_PYTHON = ROOT_DIR / "venv" / "Scripts" / "python.exe"

# Fallback to current python interpreter if venv python not found
python_executable = str(ENV_PYTHON) if ENV_PYTHON.exists() else sys.executable

print("==========================================================")
print("⚡ Launching OpsMind — AI Incident Response Agent")
print("==========================================================")

# 1. Start Backend FastAPI Server
print("🟢 [1/2] Starting Backend API Server (http://localhost:8000)...")
backend_process = subprocess.Popen(
    [python_executable, "-m", "uvicorn", "backend.main:app", "--port", "8000", "--reload"],
    cwd=str(ROOT_DIR)
)

# Wait 2 seconds for backend to initialize
time.sleep(2.5)

# 2. Start Frontend Streamlit Dashboard
print("⚡ [2/2] Starting Streamlit Dashboard (http://localhost:8501)...")
frontend_process = subprocess.Popen(
    [python_executable, "-m", "streamlit", "run", "frontend/app.py"],
    cwd=str(ROOT_DIR)
)

print("\n🚀 Both OpsMind services are running concurrently!")
print("👉 Frontend UI: http://localhost:8501")
print("👉 Backend API Docs: http://localhost:8000/docs")
print("Press Ctrl + C to stop all services.\n")

try:
    backend_process.wait()
    frontend_process.wait()
except KeyboardInterrupt:
    print("\n🛑 Shutting down OpsMind services cleanly...")
    backend_process.terminate()
    frontend_process.terminate()
    sys.exit(0)
