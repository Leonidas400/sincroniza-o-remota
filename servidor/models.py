from datetime import datetime

from pydantic import BaseModel


class FileInfo(BaseModel):
    filename: str
    size: int
    checksum: str
    modified_at: str


class UploadResponse(BaseModel):
    filename: str
    size: int
    checksum: str
    uploaded_at: str


class WSMessage(BaseModel):
    type: str
    filename: str = ""
    sender: str = ""
    files: list[FileInfo] = []
