from fastapi import APIRouter

from app.acceso.dependencias import UsuarioActualDep
from app.core.database import SessionDep

from . import service
from .schema import BienInventarioPublic

router = APIRouter(prefix="/inventario", tags=["Consultas"])


@router.get("", response_model=list[BienInventarioPublic])
def consultar_inventario(
    session: SessionDep,
    usuario: UsuarioActualDep,
    unidad_id: int | None = None,
    tipo_bien: str | None = None,
):
    return service.consultar_inventario(session, usuario, unidad_id, tipo_bien)
