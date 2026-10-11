from fastapi import APIRouter

from app.core.database import SessionDep

from . import service
from .schema import SaludPublic

router = APIRouter(prefix="/salud", tags=["Salud"])


@router.get("", response_model=SaludPublic)
def consultar_salud(session: SessionDep):
    return service.consultar(session)
