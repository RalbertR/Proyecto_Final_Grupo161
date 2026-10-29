from fastapi import APIRouter, status

from app.acceso.dependencias import UsuarioActualDep
from app.core.database import SessionDep

from . import service
from .schema import EntregaCreate, MovimientoPublic

router = APIRouter(prefix="/movimientos", tags=["Movimientos"])


@router.post(
    "/entregas", response_model=MovimientoPublic, status_code=status.HTTP_201_CREATED
)
def registrar_entrega(
    session: SessionDep, usuario: UsuarioActualDep, entrega: EntregaCreate
):
    return service.registrar_entrega(session, usuario, entrega)


@router.get("/{movimiento_id}", response_model=MovimientoPublic)
def consultar_movimiento(
    session: SessionDep, usuario: UsuarioActualDep, movimiento_id: int
):
    return service.consultar_movimiento(session, usuario, movimiento_id)
