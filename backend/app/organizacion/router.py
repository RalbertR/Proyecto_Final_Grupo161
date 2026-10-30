from fastapi import APIRouter

from app.acceso.dependencias import UsuarioActualDep
from app.acceso.service import unidades_de_destino, unidades_visibles
from app.core.database import SessionDep

from . import service
from .schema import UbicacionPublic, UnidadPublic

router = APIRouter(tags=["Organización"])


@router.get("/unidades", response_model=list[UnidadPublic])
def listar_unidades(session: SessionDep, usuario: UsuarioActualDep):
    return unidades_visibles(session, usuario)


@router.get("/unidades/destinos", response_model=list[UnidadPublic])
def listar_destinos(session: SessionDep, usuario: UsuarioActualDep):
    return unidades_de_destino(session, usuario)


@router.get("/ubicaciones", response_model=list[UbicacionPublic])
def listar_ubicaciones(session: SessionDep, usuario: UsuarioActualDep):
    return service.listar_ubicaciones(session, usuario.unidad.id)
