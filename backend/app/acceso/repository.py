from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from .model import Usuario


def buscar_por_nombre(session: Session, nombre_usuario: str) -> Usuario | None:
    return session.exec(
        select(Usuario)
        .where(Usuario.nombre_usuario == nombre_usuario)
        .options(selectinload(Usuario.unidad))
    ).first()


def buscar_por_id(session: Session, usuario_id: int) -> Usuario | None:
    return session.exec(
        select(Usuario)
        .where(Usuario.id == usuario_id)
        .options(selectinload(Usuario.unidad))
    ).first()
