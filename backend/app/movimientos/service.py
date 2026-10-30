from fastapi import HTTPException, status
from sqlalchemy import RowMapping
from sqlmodel import Session

from app.acceso.schema import UsuarioPublic
from app.acceso.service import unidades_visibles
from app.organizacion.model import Nivel, Unidad
from app.organizacion.schema import UnidadPublic
from app.organizacion.service import listar_ubicaciones

from . import repository
from .schema import (
    EntregaCreate,
    MovimientoPublic,
    RecepcionAceptada,
    RecepcionRechazada,
    RenglonPublic,
)

AREA_DEL_TIPO = {
    "ARMAMENTO": "armamento y chalecos",
    "CHALECO": "armamento y chalecos",
    "MOVIL": "móviles y equipos de comunicaciones",
    "EQUIPO_COMUNICACIONES": "móviles y equipos de comunicaciones",
}


def registrar_entrega(
    session: Session, usuario: UsuarioPublic, entrega: EntregaCreate
) -> MovimientoPublic:
    unidad_id = usuario.unidad.id
    if entrega.unidad_destino_id == unidad_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="La unidad de destino tiene que ser otra",
        )
    if session.get(Unidad, entrega.unidad_destino_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="La unidad de destino no existe",
        )
    # Se bloquean antes de validar: otra entrega de los mismos bienes espera acá
    # y, con READ COMMITTED, al seguir ve el movimiento pendiente (ADR 0001).
    ids = sorted(set(entrega.bienes))
    bienes = repository.bloquear_bienes(session, ids)
    if len(bienes) < len(ids) or any(bien.unidad_id != unidad_id for bien in bienes):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Uno de los bienes no pertenece a su unidad",
        )
    if len({AREA_DEL_TIPO[bien.tipo_bien] for bien in bienes}) > 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Un acta incluye bienes de una sola área: armamento y chalecos, "
            "o móviles y equipos de comunicaciones",
        )
    if any(bien.de_baja or bien.oficial_id is not None for bien in bienes):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Uno de los bienes no está en depósito",
        )
    if repository.alguno_con_movimiento_pendiente(session, ids):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Uno de los bienes ya tiene un movimiento pendiente",
        )
    movimiento_id = repository.insertar_entrega(
        session,
        estado_revision=(
            "NO_APLICA" if usuario.unidad.nivel == Nivel.DIRECCION else "PENDIENTE"
        ),
        numero_acta=entrega.numero_acta,
        fecha_hecho=entrega.fecha_hecho,
        descripcion=entrega.descripcion,
        usuario_id=usuario.id,
        unidad_id=unidad_id,
        unidad_destino_id=entrega.unidad_destino_id,
    )
    for bien in bienes:
        repository.insertar_renglon(session, movimiento_id, bien.id, bien.ubicacion_id)
    session.commit()
    return detalle(session, repository.buscar_cabecera(session, movimiento_id))


def consultar_movimiento(
    session: Session, usuario: UsuarioPublic, movimiento_id: int
) -> MovimientoPublic:
    cabecera = repository.buscar_cabecera(session, movimiento_id)
    if cabecera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="El movimiento no existe"
        )
    visibles = {unidad.id for unidad in unidades_visibles(session, usuario)}
    if not visibles & {cabecera["unidad_origen_id"], cabecera["unidad_destino_id"]}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene acceso a ese movimiento",
        )
    return detalle(session, cabecera)


def listar_por_recibir(
    session: Session, usuario: UsuarioPublic
) -> list[MovimientoPublic]:
    return [
        detalle(session, cabecera)
        for cabecera in repository.listar_por_recibir(session, usuario.unidad.id)
    ]


def recibir_entrega(
    session: Session,
    usuario: UsuarioPublic,
    movimiento_id: int,
    recepcion: RecepcionAceptada | RecepcionRechazada,
) -> MovimientoPublic:
    # Se bloquean antes de leer el acta: otra recepción espera acá y, con
    # READ COMMITTED, al seguir ve el acta recibida (ADR 0001).
    bienes = repository.bloquear_bienes_del_movimiento(session, movimiento_id)
    cabecera = repository.buscar_cabecera(session, movimiento_id)
    if cabecera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="El movimiento no existe"
        )
    if cabecera["unidad_destino_id"] != usuario.unidad.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo la unidad de destino recibe el acta",
        )
    # Un traslado también queda pendiente, pero lo confirma Traslados.
    if cabecera["tipo"] != "ENTREGA" or cabecera["estado"] != "PENDIENTE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El acta no está pendiente de recepción",
        )
    if isinstance(recepcion, RecepcionAceptada):
        destinos = {u.bien_id: u.ubicacion_id for u in recepcion.ubicaciones}
        propias = {
            ubicacion.id for ubicacion in listar_ubicaciones(session, usuario.unidad.id)
        }
        if destinos.keys() != set(bienes) or not set(destinos.values()) <= propias:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Indique una ubicación de su unidad para cada bien del acta",
            )
        for bien_id, ubicacion_id in destinos.items():
            repository.ubicar_renglon(session, movimiento_id, bien_id, ubicacion_id)
        repository.mover_bienes(session, movimiento_id)
        estado, motivo_rechazo = "APLICADO", None
    else:
        estado, motivo_rechazo = "RECHAZADO", recepcion.motivo_rechazo
    repository.insertar_recepcion(
        session,
        movimiento_id=movimiento_id,
        resultado=recepcion.resultado,
        motivo_rechazo=motivo_rechazo,
        usuario_id=usuario.id,
    )
    # Al pasar a aplicada, trg_mov_orden numera los renglones (ADR 0006).
    repository.cambiar_estado(session, movimiento_id, estado)
    session.commit()
    return detalle(session, repository.buscar_cabecera(session, movimiento_id))


def detalle(session: Session, cabecera: RowMapping) -> MovimientoPublic:
    return MovimientoPublic(
        **cabecera,
        unidad_origen=unidad_publica(session, cabecera["unidad_origen_id"]),
        unidad_destino=unidad_publica(session, cabecera["unidad_destino_id"]),
        bienes=[
            RenglonPublic.model_validate(renglon)
            for renglon in repository.listar_renglones(session, cabecera["id"])
        ],
    )


def unidad_publica(session: Session, unidad_id: int | None) -> UnidadPublic | None:
    unidad = session.get(Unidad, unidad_id) if unidad_id else None
    return UnidadPublic.model_validate(unidad) if unidad else None
