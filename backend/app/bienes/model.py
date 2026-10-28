from enum import Enum


class EstadoOperativo(str, Enum):
    EN_SERVICIO = "EN_SERVICIO"
    FUERA_DE_SERVICIO = "FUERA_DE_SERVICIO"


class Tenencia(str, Enum):
    DEPOSITO = "DEPOSITO"
    DOTACION = "DOTACION"
