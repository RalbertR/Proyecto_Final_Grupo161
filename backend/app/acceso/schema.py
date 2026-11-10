from pydantic import ConfigDict
from sqlmodel import SQLModel

from app.organizacion.schema import UnidadPublic


class UsuarioPublic(SQLModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 4,
                    "nombre_usuario": "aux.unidad_a",
                    "unidad": {
                        "id": 4,
                        "nombre": "Unidad Operacional A",
                        "nivel": "OPERACIONAL",
                    },
                }
            ]
        }
    )

    id: int
    nombre_usuario: str
    unidad: UnidadPublic


class SesionPublic(SQLModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "usuario": {
                        "id": 4,
                        "nombre_usuario": "aux.unidad_a",
                        "unidad": {
                            "id": 4,
                            "nombre": "Unidad Operacional A",
                            "nivel": "OPERACIONAL",
                        },
                    },
                }
            ]
        }
    )

    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioPublic
