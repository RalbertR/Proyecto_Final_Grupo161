from fastapi import HTTPException, status
from sqlalchemy import RowMapping
from sqlmodel import Session

from app.acceso.schema import UsuarioPublic
from app.acceso.service import unidades_visibles
from app.organizacion.model import Nivel, Unidad
from app.organizacion.schema import UnidadPublic

from . import repository
from .schema import EntregaCreate, MovimientoPublic, RenglonPublic

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
