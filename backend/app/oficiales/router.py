from fastapi import APIRouter

from app.acceso.dependencias import UsuarioActualDep
from app.core.database import SessionDep
from app.core.documentacion import SIN_SESION

from . import service
from .schema import OficialPublic

router = APIRouter(prefix="/oficiales", tags=["Oficiales"], responses=SIN_SESION)


@router.get(
    "",
    response_model=list[OficialPublic],
    summary="Listar los oficiales activos de la unidad",
)
def listar_oficiales(session: SessionDep, usuario: UsuarioActualDep):
    """Devuelve los oficiales activos de su unidad, que son los únicos a quienes se
    les pueden asignar bienes en dotación."""
    return service.listar_oficiales(session, usuario)
