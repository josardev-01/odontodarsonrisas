"""Validation and safe delivery of signed-document scans."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import PurePosixPath
import re

from fastapi import HTTPException, UploadFile
from fastapi.responses import Response

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class SignedAttachment:
    filename: str
    content_type: str
    data: bytes
    sha256: str

    @property
    def size(self) -> int:
        return len(self.data)


async def read_signed_attachment(file: UploadFile) -> SignedAttachment:
    data = await file.read(MAX_ATTACHMENT_BYTES + 1)
    if not data:
        raise HTTPException(status_code=422, detail="The signed document is empty")
    if len(data) > MAX_ATTACHMENT_BYTES:
        raise HTTPException(status_code=413, detail="The signed document exceeds 10 MiB")

    if data.startswith(b"%PDF-"):
        content_type, extensions = "application/pdf", {".pdf"}
    elif data.startswith(b"\xff\xd8\xff"):
        content_type, extensions = "image/jpeg", {".jpg", ".jpeg"}
    elif data.startswith(b"\x89PNG\r\n\x1a\n"):
        content_type, extensions = "image/png", {".png"}
    else:
        raise HTTPException(status_code=415, detail="Only PDF, JPEG and PNG scans are accepted")

    original = (file.filename or "").replace("\\", "/")
    filename = re.sub(r"[^A-Za-z0-9._ -]", "_", PurePosixPath(original).name).strip(" .")
    if not filename or len(filename) > 180 or PurePosixPath(filename).suffix.lower() not in extensions:
        raise HTTPException(status_code=422, detail="The document filename must match its PDF, JPEG or PNG format")
    return SignedAttachment(filename, content_type, data, sha256(data).hexdigest())


def store_attachment(record: object, attachment: SignedAttachment) -> None:
    record.attachment_filename = attachment.filename
    record.attachment_content_type = attachment.content_type
    record.attachment_size = attachment.size
    record.attachment_sha256 = attachment.sha256
    record.attachment_data = attachment.data


def attachment_response(record: object) -> Response:
    if record.attachment_data is None or record.attachment_filename is None:
        raise HTTPException(status_code=404, detail="Signed document not found")
    return Response(
        content=record.attachment_data,
        media_type=record.attachment_content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{record.attachment_filename}"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
