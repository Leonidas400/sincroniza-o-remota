import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env", encoding="utf-8")

SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "4000"))
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", ".sync_storage"))
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(50 * 1024 * 1024)))
API_KEY = os.getenv("API_KEY", "mvp-senha-facil-2026")
