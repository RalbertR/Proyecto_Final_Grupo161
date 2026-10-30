from sqlmodel import Session

from . import repository
from .schema import UbicacionPublic


def listar_ubicaciones(session: Session, unidad_id: int) -> list[UbicacionPublic]:
    return [
        UbicacionPublic.model_validate(ubicacion)
        for ubicacion in repository.listar_ubicaciones(session, unidad_id)
    ]
