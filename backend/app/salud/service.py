from sqlmodel import Session

from . import repository
from .schema import SaludPublic


def consultar(session: Session) -> SaludPublic:
    repository.verificar_conexion(session)
    return SaludPublic(estado="ok")
