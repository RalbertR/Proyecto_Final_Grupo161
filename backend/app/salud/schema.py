from pydantic import BaseModel


class SaludPublic(BaseModel):
    estado: str
