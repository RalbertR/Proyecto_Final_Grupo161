from fastapi import APIRouter

from app.acceso.dependencias import UsuarioActualDep
from app.acceso.service import unidades_de_destino, unidades_visibles
from app.core.database import SessionDep
from app.core.documentacion import SIN_SESION

from . import service
from .schema import UbicacionPublic, UnidadPublic

router = APIRouter(tags=["Organización"], responses=SIN_SESION)


@router.get(
    "/unidades",
    response_model=list[UnidadPublic],
    summary="Listar las unidades que el usuario puede consultar",
)
def listar_unidades(session: SessionDep, usuario: UsuarioActualDep):
    """Una Operacional ve solo la suya, una Regional la suya y sus Operacionales, y la
    Dirección todas. Sirve para armar el filtro del inventario."""
    return unidades_visibles(session, usuario)


@router.get(
    "/unidades/destinos",
    response_model=list[UnidadPublic],
    summary="Listar las unidades a las que se puede entregar",
)
def listar_destinos(session: SessionDep, usuario: UsuarioActualDep):
    """Devuelve todas las unidades menos la suya. Se puede entregar a cualquiera,
    aunque no dependa de la suya."""
    return unidades_de_destino(session, usuario)


@router.get(
    "/ubicaciones",
    response_model=list[UbicacionPublic],
    summary="Listar las ubicaciones de la unidad",
)
def listar_ubicaciones(session: SessionDep, usuario: UsuarioActualDep):
    """Devuelve las ubicaciones de su unidad, como Sala de Armas, Depósito o Playón.
    Se elige una al recibir una entrega o al registrar la devolución de un oficial."""
    return service.listar_ubicaciones(session, usuario.unidad.id)
