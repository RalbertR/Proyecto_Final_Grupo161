from fastapi import APIRouter

from app.acceso.dependencias import UsuarioActualDep
from app.acceso.service import unidades_visibles
from app.core.database import SessionDep

from .schema import UnidadPublic

router = APIRouter(prefix="/unidades", tags=["Organización"])


@router.get("", response_model=list[UnidadPublic])
def listar_unidades(session: SessionDep, usuario: UsuarioActualDep):
    return unidades_visibles(session, usuario)
