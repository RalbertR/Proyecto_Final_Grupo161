from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.database import SessionDep

from . import service
from .schema import UsuarioPublic

esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def usuario_actual(
    session: SessionDep, token: Annotated[str | None, Depends(esquema_oauth2)]
) -> UsuarioPublic:
    return service.usuario_del_token(session, token)


UsuarioActualDep = Annotated[UsuarioPublic, Depends(usuario_actual)]
