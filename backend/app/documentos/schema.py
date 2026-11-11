from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import SQLModel

DOCUMENTO = {
    "id": 31,
    "nombre_original": "acta_0012_2026.pdf",
    "tipo_mime": "application/pdf",
    "tamano_bytes": 482113,
    "hash_sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
    "usuario": "aux.unidad_a",
    "fecha_carga": "2026-11-09T10:21:00",
}


class DocumentoPublic(SQLModel):
    model_config = ConfigDict(json_schema_extra={"examples": [DOCUMENTO]})

    id: int
    nombre_original: str
    tipo_mime: str
    tamano_bytes: int
    hash_sha256: str
    usuario: str
    fecha_carga: datetime


class DocumentosActaPublic(SQLModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"documentos": [DOCUMENTO], "puede_adjuntar": True}]
        }
    )

    documentos: list[DocumentoPublic]
    puede_adjuntar: bool
