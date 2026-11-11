from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.core.database import SessionDep
from app.core.documentacion import SIN_SESION, error, error_422

from . import service
from .dependencias import UsuarioActualDep
from .schema import SesionPublic, UsuarioPublic

router = APIRouter(prefix="/auth", tags=["Acceso"])


@router.post(
    "/login",
    response_model=SesionPublic,
    summary="Iniciar sesión",
    responses={
        401: error(
            "El usuario no existe, la contraseña es incorrecta o el usuario está "
            "inactivo. En los tres casos el mensaje es el mismo.",
            "Usuario o contraseña incorrectos",
        ),
        422: error_422("Falta el usuario o la contraseña."),
    },
)
def iniciar_sesion(
    session: SessionDep,
    formulario: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """Inicia sesión con usuario y contraseña. Se envían como formulario, en los
    campos `username` y `password`.

    Devuelve el token de sesión, que después se manda en el encabezado
    `Authorization: Bearer <token>`, junto con los datos del usuario y de su unidad.
    """
    return service.iniciar_sesion(session, formulario.username, formulario.password)


@router.get(
    "/me",
    response_model=UsuarioPublic,
    summary="Consultar el usuario de la sesión",
    responses=SIN_SESION,
)
def consultar_usuario_actual(usuario: UsuarioActualDep):
    """Devuelve el usuario que inició la sesión y su unidad. La unidad determina qué
    bienes y qué actas puede ver."""
    return usuario
