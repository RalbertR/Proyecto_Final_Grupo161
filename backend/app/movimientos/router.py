from typing import Annotated

from fastapi import APIRouter, Body, status

from app.acceso.dependencias import UsuarioActualDep
from app.core.database import SessionDep

from . import service
from .schema import (
    EntregaCreate,
    MovimientoPublic,
    RecepcionAceptada,
    RecepcionRechazada,
)

router = APIRouter(prefix="/movimientos", tags=["Movimientos"])


@router.post(
    "/entregas", response_model=MovimientoPublic, status_code=status.HTTP_201_CREATED
)
def registrar_entrega(
    session: SessionDep, usuario: UsuarioActualDep, entrega: EntregaCreate
):
    return service.registrar_entrega(session, usuario, entrega)


@router.get("/por-recibir", response_model=list[MovimientoPublic])
def listar_por_recibir(session: SessionDep, usuario: UsuarioActualDep):
    return service.listar_por_recibir(session, usuario)


@router.get("/{movimiento_id}", response_model=MovimientoPublic)
def consultar_movimiento(
    session: SessionDep, usuario: UsuarioActualDep, movimiento_id: int
):
    return service.consultar_movimiento(session, usuario, movimiento_id)


@router.post("/{movimiento_id}/recepcion", response_model=MovimientoPublic)
def recibir_entrega(
    session: SessionDep,
    usuario: UsuarioActualDep,
    movimiento_id: int,
    recepcion: Annotated[
        RecepcionAceptada | RecepcionRechazada, Body(discriminator="resultado")
    ],
):
    return service.recibir_entrega(session, usuario, movimiento_id, recepcion)
