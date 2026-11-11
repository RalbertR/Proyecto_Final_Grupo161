from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator
from sqlmodel import SQLModel

from app.oficiales.schema import OficialPublic
from app.organizacion.schema import UnidadPublic
from app.revision.schema import RevisionPublic

Motivo = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
]


class DatosActa(BaseModel):
    numero_acta: str = Field(pattern=r"^[0-9]{4}/[0-9]{4}$")
    fecha_hecho: date
    descripcion: str | None = Field(default=None, max_length=500)

    @field_validator("fecha_hecho")
    @classmethod
    def no_posterior_a_hoy(cls, fecha_hecho: date) -> date:
        if fecha_hecho > date.today():
            raise ValueError("La fecha del hecho no puede ser posterior a hoy")
        return fecha_hecho


ACTA = {
    "numero_acta": "0012/2026",
    "fecha_hecho": "2026-11-09",
    "descripcion": "Entrega de dos armas a la Unidad B",
}


class ActaCreate(DatosActa):
    bienes: list[int] = Field(min_length=1)


class EntregaCreate(ActaCreate):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{**ACTA, "bienes": [21, 22], "unidad_destino_id": 5}]
        }
    )

    unidad_destino_id: int


class DotacionCreate(ActaCreate):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "numero_acta": "0013/2026",
                    "fecha_hecho": "2026-11-09",
                    "descripcion": "Dotación de una pistola",
                    "bienes": [31],
                    "oficial_id": 12,
                }
            ]
        }
    )

    oficial_id: int


class UbicacionDestino(BaseModel):
    bien_id: int
    ubicacion_id: int


class DevolucionCreate(DatosActa):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "numero_acta": "0014/2026",
                    "fecha_hecho": "2026-11-09",
                    "descripcion": "Devolución por pase a otra tarea",
                    "oficial_id": 12,
                    "ubicaciones": [{"bien_id": 31, "ubicacion_id": 10}],
                }
            ]
        }
    )

    oficial_id: int
    ubicaciones: list[UbicacionDestino] = Field(min_length=1)


class RecepcionAceptada(BaseModel):
    resultado: Literal["ACEPTADO"]
    ubicaciones: list[UbicacionDestino]


class RecepcionDevuelta(BaseModel):
    resultado: Literal["DEVUELTO"]
    motivo: Motivo
    bienes_con_novedad: list[int] = []


class DesistimientoCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"motivo": "El destino ya no necesita los bienes"}]
        }
    )

    motivo: Motivo


class RectificacionCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "fecha_hecho": "2026-11-08",
                    "numero_acta": "0012/2026",
                    "descripcion": "Entrega de dos armas a la Unidad B",
                    "motivo": "La fecha del acta escaneada es el 8 de noviembre",
                }
            ]
        }
    )

    fecha_hecho: date
    numero_acta: str = Field(pattern=r"^[0-9]{4}/[0-9]{4}$")
    descripcion: str | None = Field(default=None, max_length=500)
    motivo: Motivo

    @field_validator("fecha_hecho")
    @classmethod
    def no_posterior_a_hoy(cls, fecha_hecho: date) -> date:
        if fecha_hecho > date.today():
            raise ValueError("La fecha del hecho no puede ser posterior a hoy")
        return fecha_hecho


class RenglonPublic(SQLModel):
    bien_id: int
    tipo_bien: str
    identificacion: str
    marca: str
    modelo: str
    estado_operativo: str
    ubicacion_origen: str | None
    ubicacion_destino: str | None


class VersionPublic(SQLModel):
    version: int
    fecha_hecho: date
    numero_acta: str | None
    descripcion: str | None
    motivo: str | None
    usuario: str
    fecha: datetime


class NovedadPublic(SQLModel):
    bien_id: int
    identificacion: str


class RecepcionPublic(SQLModel):
    resultado: str
    motivo: str | None
    bienes_con_novedad: list[NovedadPublic]
    usuario: str
    fecha: datetime


MOVIMIENTO = {
    "id": 19,
    "tipo": "ENTREGA",
    "estado": "APLICADO",
    "estado_revision": "PENDIENTE",
    "numero_acta": "0012/2026",
    "fecha_hecho": "2026-11-09",
    "descripcion": "Entrega de dos armas a la Unidad B",
    "unidad_origen": {
        "id": 4,
        "nombre": "Unidad Operacional A",
        "nivel": "OPERACIONAL",
    },
    "unidad_destino": {
        "id": 5,
        "nombre": "Unidad Operacional B",
        "nivel": "OPERACIONAL",
    },
    "oficial_origen": None,
    "oficial_destino": None,
    "usuario": "aux.unidad_a",
    "fecha_carga": "2026-11-09T10:21:00",
    "bienes": [
        {
            "bien_id": 21,
            "tipo_bien": "ARMAMENTO",
            "identificacion": "PB-100021",
            "marca": "Bersa",
            "modelo": "Thunder 9",
            "estado_operativo": "EN_SERVICIO",
            "ubicacion_origen": "Sala de Armas",
            "ubicacion_destino": "Sala de Armas",
        }
    ],
    "version_vigente": 0,
    "versiones": [
        {
            "version": 0,
            "fecha_hecho": "2026-11-09",
            "numero_acta": "0012/2026",
            "descripcion": "Entrega de dos armas a la Unidad B",
            "motivo": None,
            "usuario": "aux.unidad_a",
            "fecha": "2026-11-09T10:21:00",
        }
    ],
    "revisiones": [],
    "recepciones": [],
    "motivo_rechazo": None,
}


class MovimientoPublic(SQLModel):
    model_config = ConfigDict(json_schema_extra={"examples": [MOVIMIENTO]})

    id: int
    tipo: str
    estado: str
    estado_revision: str
    numero_acta: str | None
    fecha_hecho: date
    descripcion: str | None
    unidad_origen: UnidadPublic | None
    unidad_destino: UnidadPublic | None
    oficial_origen: OficialPublic | None
    oficial_destino: OficialPublic | None
    usuario: str
    fecha_carga: datetime
    bienes: list[RenglonPublic]
    version_vigente: int
    versiones: list[VersionPublic]
    revisiones: list[RevisionPublic]
    recepciones: list[RecepcionPublic]
    motivo_rechazo: str | None = None
