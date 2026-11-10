from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlmodel import SQLModel

from app.bienes.model import EstadoOperativo
from app.oficiales.schema import OficialPublic


class RegistroBandejaPublic(SQLModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "registro": "MOVIMIENTO",
                    "registro_id": 19,
                    "evento": "ENTREGA",
                    "fecha": "2026-11-09",
                    "unidad_registrante": "Unidad Operacional A",
                    "usuario": "aux.unidad_a",
                    "detalle": "Entrega de dos armas a la Unidad B",
                    "version": 0,
                    "numero_acta": "0012/2026",
                    "unidad_origen": "Unidad Operacional A",
                    "unidad_destino": "Unidad Operacional B",
                    "oficial_origen": None,
                    "oficial_destino": None,
                    "bien_identificacion": None,
                    "estado_nuevo": None,
                }
            ]
        }
    )

    registro: str
    registro_id: int
    evento: str
    fecha: date
    unidad_registrante: str
    usuario: str
    detalle: str | None
    version: int
    numero_acta: str | None
    unidad_origen: str | None
    unidad_destino: str | None
    oficial_origen: OficialPublic | None
    oficial_destino: OficialPublic | None
    bien_identificacion: str | None
    estado_nuevo: EstadoOperativo | None


class RevisionRevisado(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"resultado": "REVISADO", "version": 0}]}
    )

    resultado: Literal["REVISADO"]
    version: int


class RevisionObservada(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "resultado": "OBSERVADO",
                    "version": 0,
                    "motivo_observacion": "La fecha del acta no coincide con la cargada",
                }
            ]
        }
    )

    resultado: Literal["OBSERVADO"]
    motivo_observacion: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
    ]
    version: int


class RevisionPublic(SQLModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "resultado": "OBSERVADO",
                    "version_revisada": 0,
                    "motivo_observacion": "La fecha del acta no coincide con la cargada",
                    "usuario": "logistico.regional_norte",
                    "fecha": "2026-11-10T09:30:00",
                }
            ]
        }
    )

    resultado: str
    version_revisada: int
    motivo_observacion: str | None
    usuario: str
    fecha: datetime
