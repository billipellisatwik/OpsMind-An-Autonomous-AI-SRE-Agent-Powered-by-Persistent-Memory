import os
from pathlib import Path
from dotenv import load_dotenv

# Locate project root directory (OpsMind/)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

# Load environment variables strictly from .env file
load_dotenv(dotenv_path=ENV_PATH)

# Hindsight Persistent Memory Configuration
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY", "")
HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io/v1")
HINDSIGHT_BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "opsmind-incidents")

# Local Ollama Inference Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
