from typing import Annotated

from fastapi import APIRouter, Body, status

from app.acceso.dependencias import UsuarioActualDep
from app.core.database import SessionDep
from app.core.documentacion import SIN_SESION, error, error_422

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

router = APIRouter(prefix="/movimientos", tags=["Movimientos"], responses=SIN_SESION)

NO_EXISTE = error("El movimiento no existe.", "El movimiento no existe")
BIEN_AJENO = "Uno de los bienes no pertenece a su unidad"
PENDIENTE = "Uno de los bienes ya tiene un movimiento pendiente"
UNA_SOLA_AREA = (
    "Un acta incluye bienes de una sola área: armamento y chalecos, "
    "o móviles y equipos de comunicaciones"
)
TRIGGER_PENDIENTE = "El bien tiene un movimiento pendiente y no admite otro"
ACTA_SIN_ACCESO = (
    "El acta no es de su unidad ni de una unidad que dependa de la suya, y su unidad "
    "tampoco tiene hoy ninguno de los bienes."
)


@router.post(
    "/entregas",
    response_model=MovimientoPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una entrega a otra unidad",
    responses={
        403: error("Alguno de los bienes no es de su unidad.", BIEN_AJENO),
        409: error(
            "Alguno de los bienes no está en depósito o ya está en otra acta que "
            "espera resolverse. Si dos usuarios entregan el mismo bien a la vez, el "
            "segundo recibe este error.",
            "Uno de los bienes no está en depósito",
            PENDIENTE,
            TRIGGER_PENDIENTE,
        ),
        422: error_422(
            "El destino no sirve, hay bienes de dos áreas distintas o algún dato "
            "tiene mal el formato. El número de acta es del estilo `0001/2026` y la "
            "fecha del hecho no puede ser posterior a hoy.",
            "La unidad de destino tiene que ser otra",
            "La unidad de destino no existe",
            UNA_SOLA_AREA,
        ),
    },
)
def registrar_entrega(
    session: SessionDep, usuario: UsuarioActualDep, entrega: EntregaCreate
):
    """Registra el acta de una entrega de bienes en depósito de su unidad a otra
    unidad. El acta queda pendiente de recepción.

    Hasta que el destino la acepte, los bienes siguen en el inventario de su unidad,
    marcados con un movimiento pendiente, y no se pueden usar en otro movimiento.

    Si la registra la Dirección, el acta no pasa por revisión.
    """
    return service.registrar_entrega(session, usuario, entrega)


@router.post(
    "/dotaciones",
    response_model=MovimientoPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Asignar bienes en dotación a un oficial",
    responses={
        403: error("Alguno de los bienes no es de su unidad.", BIEN_AJENO),
        409: error(
            "Alguno de los bienes está fuera de servicio, no está en depósito o tiene "
            "un movimiento pendiente. También falla si el oficial tiene un traslado "
            "pendiente o ya tiene un bien de ese tipo.",
            "Uno de los bienes está fuera de servicio",
            "Uno de los bienes no está en depósito",
            PENDIENTE,
            "El oficial tiene un traslado pendiente",
            "El oficial ya tiene asignado un bien de ese tipo",
        ),
        422: error_422(
            "El oficial no está activo o no es de su unidad, hay bienes de dos áreas "
            "distintas o hay dos bienes del mismo tipo en el acta.",
            "El oficial tiene que ser activo y de su unidad",
            UNA_SOLA_AREA,
            "Un oficial recibe un solo bien de cada tipo",
        ),
    },
)
def registrar_dotacion(
    session: SessionDep, usuario: UsuarioActualDep, dotacion: DotacionCreate
):
    """Asigna bienes de su unidad a un oficial de la misma unidad. Un oficial puede
    tener a lo sumo un bien de cada tipo.

    Se aplica en el acto, sin que nadie tenga que recibirla: los bienes pasan al
    oficial, sin ubicación, y la unidad sigue siendo la dueña. El acta queda
    pendiente de revisión de la Regional.
    """
    return service.registrar_dotacion(session, usuario, dotacion)


@router.post(
    "/devoluciones",
    response_model=MovimientoPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar la devolución de bienes de un oficial",
    responses={
        403: error("Alguno de los bienes no es de su unidad.", BIEN_AJENO),
        409: error(
            "Alguno de los bienes no está asignado a ese oficial o tiene un "
            "movimiento pendiente.",
            "Uno de los bienes no está asignado a ese oficial",
            PENDIENTE,
            TRIGGER_PENDIENTE,
        ),
        422: error_422(
            "Falta la ubicación de algún bien, es de otra unidad, hay un bien "
            "repetido o hay bienes de dos áreas distintas.",
            "Indique una ubicación de su unidad para cada bien, sin repetirlos",
            UNA_SOLA_AREA,
        ),
    },
)
def registrar_devolucion(
    session: SessionDep, usuario: UsuarioActualDep, devolucion: DevolucionCreate
):
    """Registra que un oficial devolvió bienes a la unidad.

    Se aplica en el acto: cada bien vuelve al depósito, en la ubicación que se
    indique, y deja de estar asignado al oficial. El acta queda pendiente de
    revisión de la Regional.
    """
    return service.registrar_devolucion(session, usuario, devolucion)


@router.get(
    "/por-recibir",
    response_model=list[MovimientoPublic],
    summary="Listar las actas por recibir",
)
def listar_por_recibir(session: SessionDep, usuario: UsuarioActualDep):
    """Devuelve las entregas pendientes que otra unidad le hizo a la suya, con sus
    bienes."""
    return service.listar_por_recibir(session, usuario)


@router.get(
    "/devueltas",
    response_model=list[MovimientoPublic],
    summary="Listar las actas que le devolvieron",
)
def listar_devueltas(session: SessionDep, usuario: UsuarioActualDep):
    """Devuelve las entregas de su unidad que el destino mandó de vuelta porque algo
    no coincidía. En `recepciones` está el motivo y los bienes con novedad. Su
    unidad puede corregirlas y reenviarlas, o desistir."""
    return service.listar_devueltas(session, usuario)


@router.get(
    "/observados",
    response_model=list[MovimientoPublic],
    summary="Listar los movimientos observados",
)
def listar_observados(session: SessionDep, usuario: UsuarioActualDep):
    """Devuelve los movimientos que registró su unidad y que su superior observó
    porque tenían algún error. El motivo está en `revisiones`. Se corrigen con una
    rectificación."""
    return service.listar_observados(session, usuario)


@router.get(
    "/{movimiento_id}",
    response_model=MovimientoPublic,
    summary="Consultar un acta",
    responses={
        403: error(ACTA_SIN_ACCESO, "No tiene acceso a ese movimiento"),
        404: NO_EXISTE,
        422: error_422("El identificador del movimiento no es un número."),
    },
)
def consultar_movimiento(
    session: SessionDep, usuario: UsuarioActualDep, movimiento_id: int
):
    """Devuelve el acta completa: los bienes, la versión vigente, todas las
    versiones anteriores, las revisiones y las recepciones.

    La ven las unidades de origen y de destino, las que están por encima de ellas y
    la unidad que hoy tiene alguno de los bienes."""
    return service.consultar_movimiento(session, usuario, movimiento_id)


@router.put(
    "/{movimiento_id}",
    response_model=MovimientoPublic,
    summary="Corregir y reenviar un acta devuelta",
    responses={
        403: error(
            "Solo corrige el acta la unidad que la entregó, y los bienes tienen que "
            "ser de su unidad.",
            "Solo la unidad de origen corrige el acta",
            BIEN_AJENO,
        ),
        404: NO_EXISTE,
        409: error(
            "El acta no está devuelta o alguno de los bienes ya está en otro "
            "movimiento.",
            "El acta no está devuelta",
            "Uno de los bienes no está en depósito",
            PENDIENTE,
        ),
        422: error_422(
            "La entrega corregida tiene que cumplir lo mismo que una entrega nueva.",
            "La unidad de destino tiene que ser otra",
            UNA_SOLA_AREA,
        ),
    },
)
def corregir_entrega(
    session: SessionDep,
    usuario: UsuarioActualDep,
    movimiento_id: int,
    entrega: EntregaCreate,
):
    """La unidad que entregó corrige un acta que el destino le devolvió y la vuelve
    a enviar. Lleva los mismos datos y las mismas validaciones que una entrega nueva.

    Se pueden cambiar los bienes y el destino. El número, la fecha y la descripción
    se guardan como una versión nueva, sin perder los anteriores. El acta vuelve a
    quedar pendiente de recepción.
    """
    return service.corregir_entrega(session, usuario, movimiento_id, entrega)


@router.post(
    "/{movimiento_id}/recepcion",
    response_model=MovimientoPublic,
    summary="Aceptar o devolver una entrega",
    responses={
        403: error(
            "Solo recibe el acta la unidad de destino.",
            "Solo la unidad de destino recibe el acta",
        ),
        404: NO_EXISTE,
        409: error(
            "El acta ya fue aceptada, rechazada o devuelta. Si dos usuarios la "
            "reciben a la vez, el segundo recibe este error.",
            "El acta no está pendiente de recepción",
        ),
        422: error_422(
            "Al aceptar, falta la ubicación de algún bien o es de otra unidad. Al "
            "devolver, falta el motivo o hay una novedad de un bien que no es del "
            "acta.",
            "Indique una ubicación de su unidad para cada bien del acta",
            "Las novedades tienen que ser de bienes del acta",
        ),
    },
)
def recibir_entrega(
    session: SessionDep,
    usuario: UsuarioActualDep,
    movimiento_id: int,
    recepcion: Annotated[
        RecepcionAceptada | RecepcionDevuelta,
        Body(
            discriminator="resultado",
            openapi_examples={
                "aceptar": {
                    "summary": "Aceptar y ubicar los bienes",
                    "value": {
                        "resultado": "ACEPTADO",
                        "ubicaciones": [
                            {"bien_id": 21, "ubicacion_id": 10},
                            {"bien_id": 22, "ubicacion_id": 10},
                        ],
                    },
                },
                "devolver": {
                    "summary": "Devolver al origen con novedad",
                    "value": {
                        "resultado": "DEVUELTO",
                        "motivo": "El número de serie del arma 22 no coincide con el acta",
                        "bienes_con_novedad": [22],
                    },
                },
            },
        ),
    ],
):
    """La unidad de destino resuelve la entrega. Lo que hace depende de `resultado`:

    - `ACEPTADO`: hay que indicar dónde se guarda cada bien. Los bienes pasan al
      destino y el acta queda pendiente de revisión de la Regional del origen
      (salvo que la haya registrado la Dirección).
    - `DEVUELTO`: devuelve el acta al origen con un motivo y los bienes que tenían
      novedad. Los bienes siguen en el origen y no se pueden mover hasta que el
      origen corrija el acta o desista.
    """
    return service.recibir_entrega(session, usuario, movimiento_id, recepcion)


@router.post(
    "/{movimiento_id}/desistimiento",
    response_model=MovimientoPublic,
    summary="Desistir de un acta devuelta",
    responses={
        403: error(
            "Solo desiste la unidad que hizo la entrega.",
            "Solo la unidad de origen desiste del acta",
        ),
        404: NO_EXISTE,
        409: error("El acta no está devuelta.", "El acta no está devuelta"),
        422: error_422("Falta el motivo."),
    },
)
def desistir_de_la_entrega(
    session: SessionDep,
    usuario: UsuarioActualDep,
    movimiento_id: int,
    desistimiento: DesistimientoCreate,
):
    """La unidad que entregó abandona un acta que le devolvieron. El acta queda
    rechazada y los bienes quedan libres para otros movimientos."""
    return service.desistir_de_la_entrega(
        session, usuario, movimiento_id, desistimiento
    )


@router.post(
    "/{movimiento_id}/rectificaciones",
    response_model=MovimientoPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Corregir un movimiento observado",
    responses={
        403: error(
            "Solo corrige el movimiento la unidad que lo registró.",
            "Solo la unidad que registró el movimiento lo corrige",
        ),
        404: NO_EXISTE,
        409: error(
            "El movimiento todavía espera recepción, o fue rechazado o anulado.",
            "Solo se corrigen movimientos aplicados",
        ),
        422: error_422(
            "Falta el motivo, el número de acta no es del estilo `0001/2026` o la "
            "fecha es posterior a hoy."
        ),
    },
)
def rectificar_movimiento(
    session: SessionDep,
    usuario: UsuarioActualDep,
    movimiento_id: int,
    rectificacion: RectificacionCreate,
):
    """Corrige la fecha, el número de acta o la descripción de un movimiento ya
    aplicado. Lo que estaba cargado no se pisa: la corrección queda como una versión
    nueva y el movimiento vuelve a revisión."""
    return service.rectificar_movimiento(session, usuario, movimiento_id, rectificacion)
