from fastapi import HTTPException, status
from sqlmodel import Session

from app.acceso.schema import UsuarioPublic
from app.acceso.service import unidades_visibles

from . import repository
from .schema import BienInventarioPublic, HistorialBienPublic


def consultar_inventario(
    session: Session,
    usuario: UsuarioPublic,
    unidad_id: int | None,
    tipo_bien: str | None,
) -> list[BienInventarioPublic]:
    unidades = [unidad.id for unidad in unidades_visibles(session, usuario)]
    if unidad_id is not None:
        if unidad_id not in unidades:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene acceso al inventario de esa unidad",
            )
        unidades = [unidad_id]
    filas = repository.listar_inventario(session, unidades, tipo_bien)
    return [BienInventarioPublic.model_validate(fila) for fila in filas]


def consultar_historial(
    session: Session, usuario: UsuarioPublic, bien_id: int
) -> HistorialBienPublic:
    bien = repository.buscar_bien(session, bien_id)
    if bien is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="El bien no existe"
        )
    visibles = {unidad.id for unidad in unidades_visibles(session, usuario)}
    if bien["unidad_id"] not in visibles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene acceso al historial de ese bien",
        )
    eventos = repository.listar_historial(session, bien_id)
    return HistorialBienPublic.model_validate(
        {"bien": dict(bien), "eventos": [dict(evento) for evento in eventos]}
    )
