import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env", encoding="utf-8")

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
SYNC_FOLDER = Path(os.getenv("SYNC_FOLDER", "~/Documentos/sync"))
API_KEY = os.getenv("API_KEY", "mvp-senha-facil-2026")
DEVICE_ID = os.getenv("DEVICE_ID", f"device-{uuid.uuid4().hex[:8]}")

SYNC_FOLDER = SYNC_FOLDER.expanduser()
