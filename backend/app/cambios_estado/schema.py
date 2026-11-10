from datetime import datetime
from typing import Annotated

from pydantic import ConfigDict, Field
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
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 7,
                    "bien": {
                        "id": 141,
                        "identificacion": "RD-0457",
                        "tipo_bien": "EQUIPO_COMUNICACIONES",
                        "marca": "Motorola",
                        "modelo": "DEP450",
                    },
                    "estado_anterior": "EN_SERVICIO",
                    "estado_nuevo": "FUERA_DE_SERVICIO",
                    "observaciones": "No transmite. Se golpeó en un procedimiento.",
                    "informe": {
                        "id": 33,
                        "nombre_original": "informe_RD-0457.pdf",
                        "tamano_bytes": 182311,
                    },
                    "estado": "APLICADO",
                    "estado_revision": "PENDIENTE",
                    "version_vigente": 0,
                    "unidad_registrante": "Unidad Operacional A",
                    "usuario": "aux.unidad_a",
                    "fecha": "2026-11-09T10:21:00",
                    "revisiones": [],
                    "rectificaciones": [],
                }
            ]
        }
    )

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
