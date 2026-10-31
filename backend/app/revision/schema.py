from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints
from sqlmodel import SQLModel


class RegistroBandejaPublic(SQLModel):
    registro: str
    registro_id: int
    evento: str
    fecha: date
    unidad_registrante: str
    usuario: str
    detalle: str | None
    version: int


class RevisionRevisado(BaseModel):
    resultado: Literal["REVISADO"]
    version: int


class RevisionObservada(BaseModel):
    resultado: Literal["OBSERVADO"]
    motivo_observacion: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
    ]
    version: int


class RevisionPublic(SQLModel):
    resultado: str
    version_revisada: int
    motivo_observacion: str | None
    usuario: str
    fecha: datetime
