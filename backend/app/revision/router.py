from typing import Annotated

from fastapi import APIRouter, Body, status

from app.acceso.dependencias import UsuarioActualDep
from app.core.database import SessionDep
from app.core.documentacion import SIN_SESION, error, error_422

from . import service
from .schema import (
    RegistroBandejaPublic,
    RevisionObservada,
    RevisionPublic,
    RevisionRevisado,
)

router = APIRouter(tags=["Revisión"], responses=SIN_SESION)


@router.get(
    "/revisiones/bandeja",
    response_model=list[RegistroBandejaPublic],
    summary="Listar lo que hay para revisar",
)
def listar_bandeja(session: SessionDep, usuario: UsuarioActualDep):
    """Devuelve los movimientos y cambios de estado de las unidades que dependen de
    la suya y que están esperando revisión. Una entrega que todavía no se recibió no
    aparece. Si su unidad es una Operacional, la lista siempre viene vacía."""
    return service.listar_bandeja(session, usuario)


@router.post(
    "/movimientos/{movimiento_id}/revisiones",
    response_model=RevisionPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Revisar un movimiento",
    responses={
        403: error(
            "Solo revisa la unidad que está inmediatamente por encima de la que "
            "registró el movimiento. Lo que registra la Dirección no se revisa.",
            "Solo el superior inmediato de la unidad revisa el movimiento",
        ),
        404: error("El movimiento no existe.", "El movimiento no existe"),
        409: error(
            "El movimiento ya fue revisado u observado, o la unidad que lo registró "
            "lo corrigió mientras se revisaba y `version` ya no es la vigente.",
            "El movimiento no está pendiente de revisión",
            "La revision no corresponde a la version vigente",
        ),
        422: error_422("Una observación sin motivo, o un `resultado` desconocido."),
    },
)
def revisar_movimiento(
    session: SessionDep,
    usuario: UsuarioActualDep,
    movimiento_id: int,
    revision: Annotated[
        RevisionRevisado | RevisionObservada,
        Body(
            discriminator="resultado",
            openapi_examples={
                "revisado": {
                    "summary": "Marcar como revisado",
                    "value": {"resultado": "REVISADO", "version": 0},
                },
                "observado": {
                    "summary": "Observar con un motivo",
                    "value": {
                        "resultado": "OBSERVADO",
                        "version": 0,
                        "motivo_observacion": "La fecha del acta no coincide con la cargada",
                    },
                },
            },
        ),
    ],
):
    """Marca el movimiento como revisado o lo observa, según `resultado`.

    `version` es la versión del movimiento que se estuvo mirando. Si mientras tanto
    la unidad que lo registró lo corrigió, responde 409 y hay que volver a abrir el
    acta.

    Un movimiento observado sale de la bandeja y vuelve a la unidad, que lo corrige
    con una rectificación."""
    return service.revisar_movimiento(session, usuario, movimiento_id, revision)
