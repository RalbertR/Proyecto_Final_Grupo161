from datetime import date
from typing import Literal

from sqlmodel import SQLModel

from app.bienes.model import EstadoOperativo, Tenencia
from app.organizacion.model import Nivel


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
    unidad_origen: str | None
    ubicacion_origen: str | None
    oficial_origen: str | None
    ubicacion_destino: str | None
    oficial_destino: str | None


class HistorialBienPublic(SQLModel):
    bien: BienHistorialPublic
    eventos: list[EventoHistorialPublic]


Etapa = Literal["POR_RECIBIR", "EN_REVISION", "OBSERVADA", "DEVUELTA"]


class TipoSituacion(SQLModel):
    tipo_bien: str
    total: int
    fuera_de_servicio: int


class UnidadSituacion(SQLModel):
    id: int
    nombre: str
    nivel: Nivel
    tipos: list[TipoSituacion]
    abiertas: int


class GrupoSituacion(SQLModel):
    etapa: Etapa
    cantidad: int
    dias_mas_antigua: int | None


class ActaDemorada(SQLModel):
    movimiento_id: int
    numero_acta: str | None
    etapa: Etapa
    unidad_id: int
    unidad: str
    dias: int


class SituacionPublic(SQLModel):
    unidades: list[UnidadSituacion]
    grupos: list[GrupoSituacion]
    demoradas: list[ActaDemorada]
