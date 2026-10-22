from sqlmodel import SQLModel

from .model import Nivel


class UnidadPublic(SQLModel):
    id: int
    nombre: str
    nivel: Nivel
