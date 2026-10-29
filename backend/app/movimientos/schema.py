from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator
from sqlmodel import SQLModel

from app.organizacion.schema import UnidadPublic


class EntregaCreate(BaseModel):
    unidad_destino_id: int
    numero_acta: str = Field(pattern=r"^[0-9]{4}/[0-9]{4}$")
    fecha_hecho: date
    descripcion: str | None = Field(default=None, max_length=500)
    bienes: list[int] = Field(min_length=1)

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
    ubicacion_origen: str | None
    ubicacion_destino: str | None


class MovimientoPublic(SQLModel):
    id: int
    tipo: str
    estado: str
    estado_revision: str
    numero_acta: str | None
    fecha_hecho: date
    descripcion: str | None
    unidad_origen: UnidadPublic | None
    unidad_destino: UnidadPublic | None
    usuario: str
    fecha_carga: datetime
    bienes: list[RenglonPublic]
