from fastapi import APIRouter

from app.acceso.dependencias import UsuarioActualDep
from app.core.database import SessionDep

from . import service
from .schema import BienInventarioPublic, HistorialBienPublic, SituacionPublic

router = APIRouter(tags=["Consultas"])


@router.get("/inventario", response_model=list[BienInventarioPublic])
def consultar_inventario(
    session: SessionDep,
    usuario: UsuarioActualDep,
    unidad_id: int | None = None,
    tipo_bien: str | None = None,
):
    return service.consultar_inventario(session, usuario, unidad_id, tipo_bien)


@router.get("/bienes/{bien_id}/historial", response_model=HistorialBienPublic)
def consultar_historial(session: SessionDep, usuario: UsuarioActualDep, bien_id: int):
    return service.consultar_historial(session, usuario, bien_id)


@router.get("/situacion", response_model=SituacionPublic)
def consultar_situacion(
    session: SessionDep, usuario: UsuarioActualDep, regional_id: int | None = None
):
    return service.consultar_situacion(session, usuario, regional_id)
