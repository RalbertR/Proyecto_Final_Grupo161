from fastapi import HTTPException, status
from sqlmodel import Session

from app.core.seguridad import HASH_FICTICIO, crear_token, verificar_contrasena

from . import repository
from .schema import SesionPublic, UsuarioPublic


def iniciar_sesion(
    session: Session, nombre_usuario: str, contrasena: str
) -> SesionPublic:
    usuario = repository.buscar_por_nombre(session, nombre_usuario)
    hash_guardado = usuario.hash_contrasena if usuario else HASH_FICTICIO
    contrasena_valida = verificar_contrasena(contrasena, hash_guardado)
    if usuario is None or not usuario.activo or not contrasena_valida:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return SesionPublic(
        access_token=crear_token(usuario.id),
        usuario=UsuarioPublic.model_validate(usuario),
    )
