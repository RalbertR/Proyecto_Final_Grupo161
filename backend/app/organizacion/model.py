from enum import Enum

from sqlmodel import Field, SQLModel


class Nivel(str, Enum):
    DIRECCION = "DIRECCION"
    REGIONAL = "REGIONAL"
    OPERACIONAL = "OPERACIONAL"


class Unidad(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    nivel: Nivel
    unidad_superior_id: int | None = Field(default=None, foreign_key="unidad.id")
