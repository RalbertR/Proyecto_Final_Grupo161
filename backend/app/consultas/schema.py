from sqlmodel import SQLModel

from app.bienes.model import EstadoOperativo, Tenencia


class BienInventarioPublic(SQLModel):
    unidad_id: int
    unidad: str
    bien_id: int
    tipo_bien: str
    identificacion: str
    marca: str
    modelo: str
    estado_operativo: EstadoOperativo
    tenencia: Tenencia
    ubicacion: str | None
    oficial_legajo: str | None
    oficial: str | None
    con_movimiento_pendiente: bool
