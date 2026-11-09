from datetime import date

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
    oficial_id: int | None
    oficial_legajo: str | None
    oficial: str | None
    con_movimiento_pendiente: bool


class BienHistorialPublic(SQLModel):
    id: int
    tipo_bien: str
    identificacion: str
    marca: str
    modelo: str
    unidad_id: int
    unidad: str
    estado_operativo: EstadoOperativo
    de_baja: bool
    tenencia: Tenencia
    ubicacion: str | None
    oficial_legajo: str | None
    oficial: str | None
    con_movimiento_pendiente: bool


class EventoHistorialPublic(SQLModel):
    registro: str
    registro_id: int
    orden: int | None
    evento: str
    fecha: date
    numero_acta: str | None
    estado: str | None
    estado_revision: str
    origen: str | None
    destino: str | None
    unidad_duena: str | None
    estado_operativo_nuevo: EstadoOperativo | None
    detalle: str | None
    oficial_origen_id: int | None
    oficial_destino_id: int | None
    tiene_informe: bool


class HistorialBienPublic(SQLModel):
    bien: BienHistorialPublic
    eventos: list[EventoHistorialPublic]
