import logging
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

log = logging.getLogger("client.watcher")

DEBOUNCE_SECONDS = 2


class SyncEventHandler(FileSystemEventHandler):
    def __init__(self, sync_folder: Path, on_change, on_delete=None):
        super().__init__()
        self.sync_folder = sync_folder
        self.on_change = on_change
        self.on_delete = on_delete
        self._pending: dict[str, float] = {}
        self._lock = threading.Lock()

    def _should_process(self, path: str) -> bool:
        p = Path(path)
        if p.suffix == ".tmp":
            return False
        if p.name.startswith("."):
            return False
        now = time.time()
        with self._lock:
            last = self._pending.get(path, 0)
            if now - last < DEBOUNCE_SECONDS:
                return False
            self._pending[path] = now
            return True

    def on_created(self, event: FileSystemEvent):
        if event.is_directory:
            return
        if self._should_process(event.src_path):
            log.info("Arquivo criado: %s", event.src_path)
            threading.Thread(target=self.on_change, args=(Path(event.src_path),), daemon=True).start()

    def on_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return
        if self._should_process(event.src_path):
            log.info("Arquivo modificado: %s", event.src_path)
            threading.Thread(target=self.on_change, args=(Path(event.src_path),), daemon=True).start()

    def on_moved(self, event):
        if event.is_directory:
            return
            
        src_path = Path(event.src_path)
        dest_path = Path(event.dest_path)

        if not src_path.name.startswith(".") and src_path.suffix != ".tmp":
            log.info("Renomeio detectado - Apagando antigo no servidor: %s", src_path.name)
            if self.on_delete:
                threading.Thread(target=self.on_delete, args=(src_path.name,), daemon=True).start()

        if self._should_process(event.dest_path):
            log.info("Renomeio detectado - Enviando novo para o servidor: %s", dest_path.name)
            threading.Thread(target=self.on_change, args=(dest_path,), daemon=True).start()

    def on_deleted(self, event: FileSystemEvent):
        if event.is_directory:
            return
        p = Path(event.src_path)
        if p.suffix == ".tmp" or p.name.startswith("."):
            return
        log.info("Arquivo deletado: %s", event.src_path)
        if self.on_delete:
            threading.Thread(target=self.on_delete, args=(p.name,), daemon=True).start()


def start_watching(sync_folder: Path, on_change, on_delete=None) -> Observer:
    sync_folder.mkdir(parents=True, exist_ok=True)
    handler = SyncEventHandler(sync_folder, on_change, on_delete)
    observer = Observer()
    observer.schedule(handler, str(sync_folder), recursive=True)
    observer.start()
    log.info("Watching: %s", sync_folder)
    return observer
