from fastapi import APIRouter

from app.acceso.dependencias import UsuarioActualDep
from app.core.database import SessionDep

from . import service
from .schema import OficialPublic

router = APIRouter(prefix="/oficiales", tags=["Oficiales"])


@router.get("", response_model=list[OficialPublic])
def listar_oficiales(session: SessionDep, usuario: UsuarioActualDep):
    return service.listar_oficiales(session, usuario)
