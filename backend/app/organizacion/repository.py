from sqlalchemy import RowMapping
from sqlmodel import Session, text

UBICACIONES = text(
    "SELECT id, nombre FROM ubicacion "
    "WHERE unidad_id = :unidad_id AND activa ORDER BY nombre"
)


def listar_ubicaciones(session: Session, unidad_id: int) -> list[RowMapping]:
    return list(session.exec(UBICACIONES, params={"unidad_id": unidad_id}).mappings())
