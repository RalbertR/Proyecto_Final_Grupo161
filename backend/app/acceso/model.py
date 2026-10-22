from sqlmodel import Field, Relationship, SQLModel

from app.organizacion.model import Unidad


class Usuario(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nombre_usuario: str
    hash_contrasena: str
    unidad_id: int = Field(foreign_key="unidad.id")
    activo: bool = True
    unidad: Unidad = Relationship()
