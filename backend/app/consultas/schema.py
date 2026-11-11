from datetime import date
from typing import Literal

from pydantic import ConfigDict
from sqlmodel import SQLModel

from app.bienes.model import EstadoOperativo, Tenencia
from app.organizacion.model import Nivel


class BienInventarioPublic(SQLModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "unidad_id": 4,
                    "unidad": "Unidad Operacional A",
                    "bien_id": 21,
                    "tipo_bien": "ARMAMENTO",
                    "identificacion": "PB-100021",
                    "marca": "Bersa",
                    "modelo": "Thunder 9",
                    "estado_operativo": "EN_SERVICIO",
                    "tenencia": "DOTACION",
                    "ubicacion": None,
                    "oficial_id": 12,
                    "oficial_legajo": "10003",
                    "oficial": "Acosta, Lucas",
                    "con_movimiento_pendiente": False,
                }
            ]
        }
    )

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
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "bien": {
                        "id": 21,
                        "tipo_bien": "ARMAMENTO",
                        "identificacion": "PB-100021",
                        "marca": "Bersa",
                        "modelo": "Thunder 9",
                        "unidad_id": 5,
                        "unidad": "Unidad Operacional B",
                        "estado_operativo": "EN_SERVICIO",
                        "de_baja": False,
                        "tenencia": "DEPOSITO",
                        "ubicacion": "Sala de Armas",
                        "oficial_legajo": None,
                        "oficial": None,
                        "con_movimiento_pendiente": False,
                    },
                    "eventos": [
                        {
                            "registro": "MOVIMIENTO",
                            "registro_id": 19,
                            "orden": 1,
                            "evento": "ENTREGA",
                            "fecha": "2026-11-09",
                            "numero_acta": "0012/2026",
                            "estado": "APLICADO",
                            "estado_revision": "REVISADO",
                            "origen": "Unidad Operacional A",
                            "destino": "Unidad Operacional B",
                            "unidad_duena": "Unidad Operacional B",
                            "estado_operativo_nuevo": None,
                            "detalle": None,
                            "oficial_origen_id": None,
                            "oficial_destino_id": None,
                            "tiene_informe": False,
                            "unidad_origen": "Unidad Operacional A",
                            "ubicacion_origen": "Sala de Armas",
                            "oficial_origen": None,
                            "ubicacion_destino": "Sala de Armas",
                            "oficial_destino": None,
                        }
                    ],
                }
            ]
        }
    )

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
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "unidades": [
                        {
                            "id": 4,
                            "nombre": "Unidad Operacional A",
                            "nivel": "OPERACIONAL",
                            "tipos": [
                                {
                                    "tipo_bien": "ARMAMENTO",
                                    "total": 20,
                                    "fuera_de_servicio": 1,
                                },
                                {
                                    "tipo_bien": "CHALECO",
                                    "total": 19,
                                    "fuera_de_servicio": 0,
                                },
                                {
                                    "tipo_bien": "MOVIL",
                                    "total": 6,
                                    "fuera_de_servicio": 1,
                                },
                                {
                                    "tipo_bien": "EQUIPO_COMUNICACIONES",
                                    "total": 15,
                                    "fuera_de_servicio": 1,
                                },
                            ],
                            "abiertas": 3,
                        }
                    ],
                    "grupos": [
                        {"etapa": "POR_RECIBIR", "cantidad": 5, "dias_mas_antigua": 5},
                        {"etapa": "EN_REVISION", "cantidad": 8, "dias_mas_antigua": 9},
                        {"etapa": "OBSERVADA", "cantidad": 2, "dias_mas_antigua": 4},
                        {"etapa": "DEVUELTA", "cantidad": 0, "dias_mas_antigua": None},
                    ],
                    "demoradas": [
                        {
                            "movimiento_id": 19,
                            "numero_acta": "0019/2026",
                            "etapa": "EN_REVISION",
                            "unidad_id": 2,
                            "unidad": "Unidad Regional Norte",
                            "dias": 9,
                        }
                    ],
                }
            ]
        }
    )

    unidades: list[UnidadSituacion]
    grupos: list[GrupoSituacion]
    demoradas: list[ActaDemorada]
