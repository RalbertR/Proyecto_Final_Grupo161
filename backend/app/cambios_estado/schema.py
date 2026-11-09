from datetime import datetime
from typing import Annotated

from pydantic import Field
from sqlmodel import SQLModel

from app.bienes.model import EstadoOperativo
from app.revision.schema import RevisionObservada, RevisionPublic, RevisionRevisado

Version = Annotated[int, Field(ge=0, le=65535)]


class RevisionCambioRevisado(RevisionRevisado):
    version: Version


class RevisionCambioObservada(RevisionObservada):
    version: Version


class BienDelCambio(SQLModel):
    id: int
    identificacion: str
    tipo_bien: str
    marca: str
    modelo: str


class InformePublic(SQLModel):
    id: int
    nombre_original: str
    tamano_bytes: int


class RectificacionCambioPublic(SQLModel):
    version: int
    motivo: str
    usuario: str
    fecha: datetime


class CambioEstadoPublic(SQLModel):
    id: int
    bien: BienDelCambio
    estado_anterior: EstadoOperativo
    estado_nuevo: EstadoOperativo
    observaciones: str
    informe: InformePublic | None
    estado: str
    estado_revision: str
    version_vigente: int
    unidad_registrante: str
    usuario: str
    fecha: datetime
    revisiones: list[RevisionPublic]
    rectificaciones: list[RectificacionCambioPublic]
