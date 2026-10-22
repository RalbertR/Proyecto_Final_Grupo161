from sqlalchemy.orm import selectinload
from sqlmodel import Session, or_, select

from app.organizacion.model import Unidad

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


def listar_unidades(session: Session) -> list[Unidad]:
    return list(session.exec(select(Unidad).order_by(Unidad.id)))


def listar_unidad_y_dependientes(session: Session, unidad_id: int) -> list[Unidad]:
    return list(
        session.exec(
            select(Unidad)
            .where(or_(Unidad.id == unidad_id, Unidad.unidad_superior_id == unidad_id))
            .order_by(Unidad.id)
        )
    )
