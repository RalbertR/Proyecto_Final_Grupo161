from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.core.database import SessionDep

from . import service
from .schema import SesionPublic

router = APIRouter(prefix="/auth", tags=["Acceso"])


@router.post("/login", response_model=SesionPublic)
def iniciar_sesion(
    session: SessionDep,
    formulario: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    return service.iniciar_sesion(session, formulario.username, formulario.password)
