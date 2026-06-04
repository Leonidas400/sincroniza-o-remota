import hashlib
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from servidor.config import STORAGE_DIR


def ensure_storage_dir():
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def file_path(filename: str) -> Path:
    safe = Path(filename).name
    return STORAGE_DIR / safe


def save_file(filename: str, content: bytes) -> dict:
    ensure_storage_dir()
    path = file_path(filename)
    path.write_bytes(content)
    info = get_file_info(filename)
    return info


def get_file(filename: str) -> Path | None:
    path = file_path(filename)
    if path.exists():
        return path
    return None


def list_files() -> list[dict]:
    ensure_storage_dir()
    files = []
    for f in STORAGE_DIR.iterdir():
        if f.is_file():
            files.append(get_file_info(f.name))
    return files


def file_exists(filename: str) -> bool:
    return file_path(filename).exists()


def delete_file(filename: str) -> bool:
    path = file_path(filename)
    if path.exists():
        path.unlink()
        return True
    return False


def get_file_info(filename: str) -> dict:
    path = file_path(filename)
    if not path.exists():
        return {}
    stat = path.stat()
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "filename": path.name,
        "size": stat.st_size,
        "checksum": checksum,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }
