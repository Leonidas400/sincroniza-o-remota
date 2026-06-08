import hashlib
import logging
import time
from pathlib import Path

import requests

from cliente.config import API_KEY, DEVICE_ID, SERVER_URL

log = logging.getLogger("client.sync")
log.info("Config: SERVER_URL=%s | API_KEY=%s | DEVICE_ID=%s", SERVER_URL, API_KEY[:8] + "...", DEVICE_ID)

MAX_RETRIES = 3
RETRY_BACKOFF = [1, 2, 4]


def _headers():
    return {"X-API-Key": API_KEY, "X-Device-Id": DEVICE_ID}


def upload_file(filepath: Path) -> dict | None:
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(
                f"{SERVER_URL}/upload",
                headers=_headers(),
                files={"file": (filepath.name, filepath.read_bytes())},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            log.info("Upload OK: %s", filepath.name)
            return data
        except requests.RequestException as e:
            wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
            log.warning("Upload falhou (%s), retry em %ds...", e, wait)
            time.sleep(wait)
    log.error("Upload falhou definitivamente: %s", filepath.name)
    return None


def download_file(filename: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".sync_tmp")

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(
                f"{SERVER_URL}/download/{filename}",
                headers=_headers(),
                timeout=30,
            )
            resp.raise_for_status()
            tmp.write_bytes(resp.content)
            tmp.replace(dest)
            log.info("Download OK: %s", filename)
            return True
        except requests.RequestException as e:
            wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
            log.warning("Download falhou (%s), retry em %ds...", e, wait)
            time.sleep(wait)

    if tmp.exists():
        tmp.unlink()
    log.error("Download falhou definitivamente: %s", filename)
    return False


def delete_remote_file(filename: str) -> bool:
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.delete(
                f"{SERVER_URL}/delete/{filename}",
                headers=_headers(),
                timeout=30,
            )
            resp.raise_for_status()
            log.info("Delete remoto OK: %s", filename)
            return True
        except requests.RequestException as e:
            wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
            log.warning("Delete falhou (%s), retry em %ds...", e, wait)
            time.sleep(wait)
    log.error("Delete falhou definitivamente: %s", filename)
    return False


def get_server_files() -> list[dict]:
    try:
        resp = requests.get(f"{SERVER_URL}/files", headers=_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        log.error("Falha ao listar arquivos: %s", e)
        return []


def local_checksum(filepath: Path) -> str:
    return hashlib.sha256(filepath.read_bytes()).hexdigest()


def sync_initial(sync_folder: Path):
    server_files = get_server_files()
    local_files = {f.name: f for f in sync_folder.iterdir() if f.is_file()} if sync_folder.exists() else {}

    for sf in server_files:
        name = sf["filename"]
        if name in local_files:
            if local_checksum(local_files[name]) == sf["checksum"]:
                continue
        log.info("Sync download: %s", name)
        download_file(name, sync_folder / name)

    local_names = {f.name for f in local_files.values()}
    server_names = {sf["filename"] for sf in server_files}

    for name in local_names - server_names:
        log.info("Sync upload: %s", name)
        upload_file(local_files[name])
