import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, Header, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from servidor.config import API_KEY, MAX_FILE_SIZE, SERVER_HOST, SERVER_PORT, STORAGE_DIR
from servidor.models import FileInfo, UploadResponse, WSMessage
from servidor.storage import (
    delete_file,
    ensure_storage_dir,
    get_file,
    get_file_info,
    list_files,
    save_file,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("server")

app = FastAPI(title="Sync Server")

connected_clients: dict[str, WebSocket] = {}


def check_api_key(x_api_key: str | None = Header(default=None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key invalida")


@app.on_event("startup")
async def startup():
    ensure_storage_dir()
    log.info("Servidor iniciado. Storage: %s", STORAGE_DIR.resolve())


@app.get("/health")
async def health():
    return {"status": "ok", "files": len(list_files())}


@app.get("/files", response_model=list[FileInfo])
async def get_files(x_api_key: str = Header()):
    check_api_key(x_api_key)
    return list_files()


@app.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...), x_api_key: str = Header(), x_device_id: str = Header(default="")):
    check_api_key(x_api_key)

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"Arquivo excede {MAX_FILE_SIZE} bytes")

    filename = Path(file.filename).name
    info = save_file(filename, content)
    log.info("Upload: %s (%d bytes) de %s", filename, info["size"], x_device_id or "desconhecido")

    msg = WSMessage(type="FILE_UPDATED", filename=filename, sender=x_device_id)
    await broadcast(msg, exclude=x_device_id)

    return UploadResponse(
        filename=info["filename"],
        size=info["size"],
        checksum=info["checksum"],
        uploaded_at=info["modified_at"],
    )


@app.get("/download/{filename}")
async def download(filename: str, x_api_key: str = Header()):
    check_api_key(x_api_key)

    path = get_file(filename)
    if not path:
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado")

    return FileResponse(path=path, filename=filename, media_type="application/octet-stream")


@app.delete("/delete/{filename}")
async def delete(filename: str, x_api_key: str = Header(), x_device_id: str = Header(default="")):
    check_api_key(x_api_key)

    if delete_file(filename):
        log.info("Deletado: %s por %s", filename, x_device_id or "desconhecido")
        msg = WSMessage(type="FILE_DELETED", filename=filename, sender=x_device_id)
        await broadcast(msg, exclude=x_device_id)
        return {"deleted": True}

    raise HTTPException(status_code=404, detail="Arquivo nao encontrado")


async def broadcast(msg: WSMessage, exclude: str = ""):
    dead = []
    for device_id, ws in connected_clients.items():
        if device_id == exclude:
            continue
        try:
            await ws.send_text(msg.model_dump_json())
        except Exception:
            dead.append(device_id)
    for d in dead:
        connected_clients.pop(d, None)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    device_id = websocket.query_params.get("device_id", "anon")

    connected_clients[device_id] = websocket
    log.info("WS conectado: %s (total: %d)", device_id, len(connected_clients))

    files_msg = WSMessage(type="INIT", files=[FileInfo(**f) for f in list_files()])
    await websocket.send_text(files_msg.model_dump_json())

    try:
        while True:
            data = await websocket.receive_text()
            log.debug("WS recebido de %s: %s", device_id, data)
    except WebSocketDisconnect:
        pass
    finally:
        connected_clients.pop(device_id, None)
        log.info("WS desconectado: %s (total: %d)", device_id, len(connected_clients))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("servidor.main:app", host=SERVER_HOST, port=SERVER_PORT, reload=True)
