from sqlmodel import SQLModel

from app.organizacion.schema import UnidadPublic


class UsuarioPublic(SQLModel):
    id: int
    nombre_usuario: str
    unidad: UnidadPublic


class SesionPublic(SQLModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioPublic
