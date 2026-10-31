from typing import Annotated

from fastapi import APIRouter, Body, status

from app.acceso.dependencias import UsuarioActualDep
from app.core.database import SessionDep

from . import service
from .schema import (
    RegistroBandejaPublic,
    RevisionObservada,
    RevisionPublic,
    RevisionRevisado,
)

router = APIRouter(tags=["Revisión"])


@router.get("/revisiones/bandeja", response_model=list[RegistroBandejaPublic])
def listar_bandeja(session: SessionDep, usuario: UsuarioActualDep):
    return service.listar_bandeja(session, usuario)


@router.post(
    "/movimientos/{movimiento_id}/revisiones",
    response_model=RevisionPublic,
    status_code=status.HTTP_201_CREATED,
)
def revisar_movimiento(
    session: SessionDep,
    usuario: UsuarioActualDep,
    movimiento_id: int,
    revision: Annotated[
        RevisionRevisado | RevisionObservada, Body(discriminator="resultado")
    ],
):
    return service.revisar_movimiento(session, usuario, movimiento_id, revision)
