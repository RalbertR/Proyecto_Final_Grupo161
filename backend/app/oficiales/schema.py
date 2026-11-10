from pydantic import ConfigDict
from sqlmodel import SQLModel


class OficialPublic(SQLModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"id": 12, "legajo": "10003", "nombre": "Acosta, Lucas"}]
        }
    )

    id: int
    legajo: str
    nombre: str
