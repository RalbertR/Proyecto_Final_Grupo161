from datetime import datetime

from sqlmodel import SQLModel


class DocumentoPublic(SQLModel):
    id: int
    nombre_original: str
    tipo_mime: str
    tamano_bytes: int
    hash_sha256: str
    usuario: str
    fecha_carga: datetime


class DocumentosActaPublic(SQLModel):
    documentos: list[DocumentoPublic]
    puede_adjuntar: bool
