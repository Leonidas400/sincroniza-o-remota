import json
import logging
import signal
import sys
import threading
import time
from pathlib import Path

import websocket

from cliente.config import API_KEY, DEVICE_ID, SERVER_URL, SYNC_FOLDER
from cliente.sync import delete_remote_file, download_file, sync_initial, upload_file
from cliente.watcher import start_watching

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("client")

WS_RECONNECT_DELAY = 5
WS_MAX_RECONNECT = 10

_server_files: dict[str, dict] = {}
_lock = threading.Lock()
_downloading = set()
_deleting = set()


def _ws_headers():
    return {"X-API-Key": API_KEY}


def _on_change(filepath: Path):
    if filepath in _downloading or filepath.name in _deleting:
        return
    if not filepath.exists():
        return
    log.info("Mudanca detectada, upload: %s", filepath.name)
    upload_file(filepath)


def _on_delete(filename: str):
    if filename in _deleting:
        return
    log.info("Delete detectado, removendo do servidor: %s", filename)
    delete_remote_file(filename)


def _on_ws_message(ws, message):
    try:
        msg = json.loads(message)
    except json.JSONDecodeError:
        return

    msg_type = msg.get("type")

    if msg_type == "INIT":
        with _lock:
            _server_files.clear()
            for f in msg.get("files", []):
                _server_files[f["filename"]] = f
        log.info("Servidor tem %d arquivos", len(_server_files))
        _sync_from_server()
        return

    filename = msg.get("filename", "")
    sender = msg.get("sender", "")

    if sender == DEVICE_ID:
        return

    if msg_type == "FILE_UPDATED":
        log.info("Arquivo atualizado no servidor: %s", filename)
        _downloading.add(SYNC_FOLDER / filename)
        try:
            download_file(filename, SYNC_FOLDER / filename)
        finally:
            _downloading.discard(SYNC_FOLDER / filename)

    elif msg_type == "FILE_DELETED":
        log.info("Arquivo deletado no servidor: %s", filename)
        local = SYNC_FOLDER / filename
        _deleting.add(filename)
        try:
            if local.exists():
                local.unlink()
        finally:
            _deleting.discard(filename)




def _sync_from_server():
    with _lock:
        for name, info in _server_files.items():
            local = SYNC_FOLDER / name
            if not local.exists():
                log.info("Baixando do servidor: %s", name)
                _downloading.add(local)
                try:
                    download_file(name, local)
                finally:
                    _downloading.discard(local)


def _run_ws():
    url = SERVER_URL.strip()
    if url.startswith("https://"):
        url = "wss://" + url[len("https://"):]
    elif url.startswith("http://"):
        url = "ws://" + url[len("http://"):]
    elif not url.startswith("ws"):
        url = "wss://" + url
    ws_url = f"{url}/ws?device_id={DEVICE_ID}"
    reconnects = 0

    while reconnects < WS_MAX_RECONNECT:
        try:
            log.info("Conectando WS: %s", ws_url)
            ws = websocket.WebSocketApp(
                ws_url,
                header={"X-API-Key": API_KEY},
                on_message=_on_ws_message,
                on_error=lambda ws, e: log.error("WS erro: %s", e),
                on_close=lambda ws, c, m: log.info("WS fechado"),
                on_open=lambda ws: log.info("WS conectado"),
            )
            reconnects = 0
            ws.run_forever()
        except Exception as e:
            log.error("WS falhou: %s", e)

        reconnects += 1
        log.info("Reconectando WS em %ds (tentativa %d/%d)...", WS_RECONNECT_DELAY, reconnects, WS_MAX_RECONNECT)
        time.sleep(WS_RECONNECT_DELAY)

    log.error("Maximo de reconexoes WS atingido. Encerrando.")
    sys.exit(1)


def main():
    SYNC_FOLDER.mkdir(parents=True, exist_ok=True)

    log.info("Device: %s | Servidor: %s | Pasta: %s", DEVICE_ID, SERVER_URL, SYNC_FOLDER)

    log.info("Sincronizacao inicial...")
    sync_initial(SYNC_FOLDER)

    ws_thread = threading.Thread(target=_run_ws, daemon=True)
    ws_thread.start()

    observer = start_watching(SYNC_FOLDER, _on_change, _on_delete)

    def shutdown(sig, frame):
        log.info("Encerrando...")
        observer.stop()
        observer.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    log.info("Cliente rodando. Ctrl+C para encerrar.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown(None, None)


if __name__ == "__main__":
    main()
