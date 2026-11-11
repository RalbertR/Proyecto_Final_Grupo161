from pydantic import ConfigDict
from sqlmodel import SQLModel

from .model import Nivel


class UnidadPublic(SQLModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"id": 4, "nombre": "Unidad Operacional A", "nivel": "OPERACIONAL"}
            ]
        }
    )

    id: int
    nombre: str
    nivel: Nivel


class UbicacionPublic(SQLModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"id": 10, "nombre": "Sala de Armas"}]}
    )

    id: int
    nombre: str
