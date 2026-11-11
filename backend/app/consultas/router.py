from typing import Annotated

from fastapi import APIRouter, Query

from app.acceso.dependencias import UsuarioActualDep
from app.core.database import SessionDep
from app.core.documentacion import SIN_SESION, error, error_422

from . import service
from .schema import BienInventarioPublic, HistorialBienPublic, SituacionPublic

router = APIRouter(tags=["Consultas"], responses=SIN_SESION)


@router.get(
    "/inventario",
    response_model=list[BienInventarioPublic],
    summary="Consultar el inventario",
    responses={
        403: error(
            "La unidad que pidió no es de su unidad ni depende de ella.",
            "No tiene acceso al inventario de esa unidad",
        ),
        422: error_422("`unidad_id` no es un número."),
    },
)
def consultar_inventario(
    session: SessionDep,
    usuario: UsuarioActualDep,
    unidad_id: Annotated[
        int | None,
        Query(description="Muestra solo los bienes de esta unidad.", examples=[4]),
    ] = None,
    tipo_bien: Annotated[
        str | None,
        Query(
            description="Muestra solo un tipo de bien: `ARMAMENTO`, `CHALECO`, "
            "`MOVIL` o `EQUIPO_COMUNICACIONES`.",
            examples=["ARMAMENTO"],
        ),
    ] = None,
):
    """Devuelve los bienes de su unidad y de las que dependen de ella. Una Operacional
    ve solo los suyos, una Regional los suyos y los de sus Operacionales, y la
    Dirección los de todas.

    Cada bien trae su estado y quién lo tiene: la ubicación si está en depósito, o el
    oficial si está en dotación. Los dados de baja no aparecen.
    `con_movimiento_pendiente` marca los bienes que están en un acta sin resolver y
    por eso no se pueden usar en otro movimiento.
    """
    return service.consultar_inventario(session, usuario, unidad_id, tipo_bien)


@router.get(
    "/bienes/{bien_id}/historial",
    response_model=HistorialBienPublic,
    summary="Consultar el historial de un bien",
    responses={
        403: error(
            "El bien es de una unidad que no es la suya ni depende de ella.",
            "No tiene acceso al historial de ese bien",
        ),
        404: error("El bien no existe.", "El bien no existe"),
        422: error_422("El identificador del bien no es un número."),
    },
)
def consultar_historial(session: SessionDep, usuario: UsuarioActualDep, bien_id: int):
    """Devuelve cómo está hoy el bien y todo lo que le pasó: primero los movimientos
    aplicados, en el orden en que ocurrieron, y después los que siguen pendientes,
    rechazados o devueltos. También incluye sus cambios de estado de servicio.

    Cada hecho dice qué unidad era la dueña en ese momento, de dónde salió el bien y
    adónde fue, y cómo va su revisión. Si un movimiento se corrigió, se ve con los
    datos de la última versión.
    """
    return service.consultar_historial(session, usuario, bien_id)


@router.get(
    "/situacion",
    response_model=SituacionPublic,
    summary="Consultar la sala de situación",
    responses={
        403: error(
            "Un usuario de una Unidad Operacional no puede ver la sala.",
            "La sala de situación es para la Regional y la Dirección",
        ),
        422: error_422(
            "`regional_id` solo lo puede usar la Dirección y tiene que ser una "
            "Regional.",
            "Solo la Dirección elige una Regional",
            "La unidad elegida no es una Regional",
        ),
    },
)
def consultar_situacion(
    session: SessionDep,
    usuario: UsuarioActualDep,
    regional_id: Annotated[
        int | None,
        Query(
            description="Solo para la Dirección: muestra esa Regional y sus unidades.",
            examples=[2],
        ),
    ] = None,
):
    """Muestra dónde se demoran las actas y cuánto equipamiento está fuera de
    servicio en cada unidad que le corresponde ver.

    Cuenta los bienes de cada unidad por tipo, las actas abiertas según la etapa en
    la que están, los días que lleva la más antigua de cada etapa y las cinco más
    demoradas. Hay más detalle en `docs/contratos/situacion.md`.
    """
    return service.consultar_situacion(session, usuario, regional_id)
