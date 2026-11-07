from sqlmodel import SQLModel


class OficialPublic(SQLModel):
    id: int
    legajo: str
    nombre: str
