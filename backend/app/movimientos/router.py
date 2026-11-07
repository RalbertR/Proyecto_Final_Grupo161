from typing import Annotated

from fastapi import APIRouter, Body, status

from app.acceso.dependencias import UsuarioActualDep
from app.core.database import SessionDep

from . import service
from .schema import (
    DesistimientoCreate,
    DevolucionCreate,
    DotacionCreate,
    EntregaCreate,
    MovimientoPublic,
    RecepcionAceptada,
    RecepcionDevuelta,
    RectificacionCreate,
)

router = APIRouter(prefix="/movimientos", tags=["Movimientos"])


@router.post(
    "/entregas", response_model=MovimientoPublic, status_code=status.HTTP_201_CREATED
)
def registrar_entrega(
    session: SessionDep, usuario: UsuarioActualDep, entrega: EntregaCreate
):
    return service.registrar_entrega(session, usuario, entrega)


@router.post(
    "/dotaciones", response_model=MovimientoPublic, status_code=status.HTTP_201_CREATED
)
def registrar_dotacion(
    session: SessionDep, usuario: UsuarioActualDep, dotacion: DotacionCreate
):
    return service.registrar_dotacion(session, usuario, dotacion)


@router.post(
    "/devoluciones",
    response_model=MovimientoPublic,
    status_code=status.HTTP_201_CREATED,
)
def registrar_devolucion(
    session: SessionDep, usuario: UsuarioActualDep, devolucion: DevolucionCreate
):
    return service.registrar_devolucion(session, usuario, devolucion)


@router.get("/por-recibir", response_model=list[MovimientoPublic])
def listar_por_recibir(session: SessionDep, usuario: UsuarioActualDep):
    return service.listar_por_recibir(session, usuario)


@router.get("/devueltas", response_model=list[MovimientoPublic])
def listar_devueltas(session: SessionDep, usuario: UsuarioActualDep):
    return service.listar_devueltas(session, usuario)


@router.get("/observados", response_model=list[MovimientoPublic])
def listar_observados(session: SessionDep, usuario: UsuarioActualDep):
    return service.listar_observados(session, usuario)


@router.get("/{movimiento_id}", response_model=MovimientoPublic)
def consultar_movimiento(
    session: SessionDep, usuario: UsuarioActualDep, movimiento_id: int
):
    return service.consultar_movimiento(session, usuario, movimiento_id)


@router.put("/{movimiento_id}", response_model=MovimientoPublic)
def corregir_entrega(
    session: SessionDep,
    usuario: UsuarioActualDep,
    movimiento_id: int,
    entrega: EntregaCreate,
):
    return service.corregir_entrega(session, usuario, movimiento_id, entrega)


@router.post("/{movimiento_id}/recepcion", response_model=MovimientoPublic)
def recibir_entrega(
    session: SessionDep,
    usuario: UsuarioActualDep,
    movimiento_id: int,
    recepcion: Annotated[
        RecepcionAceptada | RecepcionDevuelta, Body(discriminator="resultado")
    ],
):
    return service.recibir_entrega(session, usuario, movimiento_id, recepcion)


@router.post("/{movimiento_id}/desistimiento", response_model=MovimientoPublic)
def desistir_de_la_entrega(
    session: SessionDep,
    usuario: UsuarioActualDep,
    movimiento_id: int,
    desistimiento: DesistimientoCreate,
):
    return service.desistir_de_la_entrega(
        session, usuario, movimiento_id, desistimiento
    )


@router.post(
    "/{movimiento_id}/rectificaciones",
    response_model=MovimientoPublic,
    status_code=status.HTTP_201_CREATED,
)
def rectificar_movimiento(
    session: SessionDep,
    usuario: UsuarioActualDep,
    movimiento_id: int,
    rectificacion: RectificacionCreate,
):
    return service.rectificar_movimiento(session, usuario, movimiento_id, rectificacion)
