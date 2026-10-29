from fastapi import HTTPException, status
from sqlmodel import Session

from app.core.seguridad import (
    HASH_FICTICIO,
    crear_token,
    leer_token,
    verificar_contrasena,
)
from app.organizacion.model import Nivel
from app.organizacion.schema import UnidadPublic

from . import repository
from .schema import SesionPublic, UsuarioPublic


def no_autenticado(detalle: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detalle,
        headers={"WWW-Authenticate": "Bearer"},
    )


def iniciar_sesion(
    session: Session, nombre_usuario: str, contrasena: str
) -> SesionPublic:
    usuario = repository.buscar_por_nombre(session, nombre_usuario)
    hash_guardado = usuario.hash_contrasena if usuario else HASH_FICTICIO
    contrasena_valida = verificar_contrasena(contrasena, hash_guardado)
    if usuario is None or not usuario.activo or not contrasena_valida:
        raise no_autenticado("Usuario o contraseña incorrectos")
    return SesionPublic(
        access_token=crear_token(usuario.id),
        usuario=UsuarioPublic.model_validate(usuario),
    )


def usuario_del_token(session: Session, token: str | None) -> UsuarioPublic:
    usuario_id = leer_token(token) if token else None
    usuario = repository.buscar_por_id(session, usuario_id) if usuario_id else None
    if usuario is None or not usuario.activo:
        raise no_autenticado("Sesión no válida o vencida")
    return UsuarioPublic.model_validate(usuario)


def unidades_visibles(session: Session, usuario: UsuarioPublic) -> list[UnidadPublic]:
    propia = usuario.unidad
    if propia.nivel == Nivel.OPERACIONAL:
        return [propia]
    if propia.nivel == Nivel.REGIONAL:
        unidades = repository.listar_unidad_y_dependientes(session, propia.id)
    else:
        unidades = repository.listar_unidades(session)
    return [UnidadPublic.model_validate(unidad) for unidad in unidades]


def unidades_de_destino(session: Session, usuario: UsuarioPublic) -> list[UnidadPublic]:
    return [
        UnidadPublic.model_validate(unidad)
        for unidad in repository.listar_unidades(session)
        if unidad.id != usuario.unidad.id
    ]
