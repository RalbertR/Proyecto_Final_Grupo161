from fastapi import HTTPException, status
from sqlalchemy import Row, RowMapping
from sqlmodel import Session

from app.acceso.schema import UsuarioPublic
from app.acceso.service import unidades_visibles
from app.oficiales import repository as oficiales
from app.oficiales.service import oficial_publico
from app.organizacion.model import Nivel, Unidad
from app.organizacion.schema import UnidadPublic
from app.organizacion.service import listar_ubicaciones
from app.revision.repository import (
    bloquear_movimiento,
    cambiar_estado_revision,
    listar_revisiones,
)
from app.revision.schema import RevisionPublic

from . import repository
from .schema import (
    ActaCreate,
    DesistimientoCreate,
    DotacionCreate,
    EntregaCreate,
    MovimientoPublic,
    NovedadPublic,
    RecepcionAceptada,
    RecepcionDevuelta,
    RecepcionPublic,
    RectificacionCreate,
    RenglonPublic,
    VersionPublic,
)

AREA_DEL_TIPO = {
    "ARMAMENTO": "armamento y chalecos",
    "CHALECO": "armamento y chalecos",
    "MOVIL": "móviles y equipos de comunicaciones",
    "EQUIPO_COMUNICACIONES": "móviles y equipos de comunicaciones",
}


def validar_entrega(
    session: Session,
    unidad_id: int,
    entrega: EntregaCreate,
    bienes: list[Row],
    excluir: int = 0,
) -> None:
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
    validar_bienes(session, unidad_id, entrega, bienes, excluir)


def validar_bienes(
    session: Session,
    unidad_id: int,
    acta: ActaCreate,
    bienes: list[Row],
    excluir: int = 0,
) -> None:
    ids = sorted(set(acta.bienes))
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
    if repository.alguno_con_movimiento_pendiente(session, ids, excluir):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Uno de los bienes ya tiene un movimiento pendiente",
        )


def registrar_entrega(
    session: Session, usuario: UsuarioPublic, entrega: EntregaCreate
) -> MovimientoPublic:
    unidad_id = usuario.unidad.id
    # Se bloquean antes de validar: otra entrega de los mismos bienes espera acá
    # y, con READ COMMITTED, al seguir ve el movimiento pendiente (ADR 0001).
    bienes = repository.bloquear_bienes(session, sorted(set(entrega.bienes)))
    validar_entrega(session, unidad_id, entrega, bienes)
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


def validar_oficial(session: Session, unidad_id: int, oficial_id: int) -> None:
    oficial = oficiales.buscar(session, oficial_id)
    if oficial is None or oficial["unidad_id"] != unidad_id or not oficial["activo"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El oficial tiene que ser activo y de su unidad",
        )


def registrar_dotacion(
    session: Session, usuario: UsuarioPublic, dotacion: DotacionCreate
) -> MovimientoPublic:
    unidad_id = usuario.unidad.id
    # Se bloquean antes de validar: otra operación sobre los mismos bienes espera
    # acá y, con READ COMMITTED, al seguir ve su resultado (ADR 0001).
    bienes = repository.bloquear_bienes(session, sorted(set(dotacion.bienes)))
    validar_oficial(session, unidad_id, dotacion.oficial_id)
    validar_bienes(session, unidad_id, dotacion, bienes)
    # RN-08: un bien fuera de servicio no se asigna en dotación.
    if any(bien.estado_operativo == "FUERA_DE_SERVICIO" for bien in bienes):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Uno de los bienes está fuera de servicio",
        )
    # RN-10: un oficial con un traslado pendiente no recibe dotaciones.
    if oficiales.tiene_traslado_pendiente(session, dotacion.oficial_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El oficial tiene un traslado pendiente",
        )
    # RN-11: se aplica en el acto, sin recepción. Los renglones se insertan con el
    # acta ya aplicada, así trg_mb_orden les da su número de orden (ADR 0006).
    movimiento_id = repository.insertar_dotacion(
        session,
        estado_revision=(
            "NO_APLICA" if usuario.unidad.nivel == Nivel.DIRECCION else "PENDIENTE"
        ),
        numero_acta=dotacion.numero_acta,
        fecha_hecho=dotacion.fecha_hecho,
        descripcion=dotacion.descripcion,
        usuario_id=usuario.id,
        unidad_id=unidad_id,
        oficial_id=dotacion.oficial_id,
    )
    for bien in bienes:
        repository.insertar_renglon(session, movimiento_id, bien.id, bien.ubicacion_id)
    repository.asignar_bienes(session, movimiento_id)
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
    relacionadas = {
        cabecera["unidad_origen_id"],
        cabecera["unidad_destino_id"],
        *repository.unidades_actuales_de_los_bienes(session, movimiento_id),
    }
    if not visibles & relacionadas:
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
    recepcion: RecepcionAceptada | RecepcionDevuelta,
) -> MovimientoPublic:
    # Se bloquean el acta y sus bienes antes de leerla: otra recepción espera acá
    # y, con READ COMMITTED, al seguir ve el acta recibida (ADR 0001).
    bloquear_movimiento(session, movimiento_id)
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
        estado, motivo, novedades = "APLICADO", None, set()
    else:
        novedades = set(recepcion.bienes_con_novedad)
        if not novedades <= set(bienes):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Las novedades tienen que ser de bienes del acta",
            )
        estado, motivo = "DEVUELTO", recepcion.motivo
    recepcion_id = repository.insertar_recepcion(
        session,
        movimiento_id=movimiento_id,
        resultado=recepcion.resultado,
        motivo=motivo,
        usuario_id=usuario.id,
    )
    for bien_id in sorted(novedades):
        repository.insertar_novedad(session, recepcion_id, bien_id)
    # Al pasar a aplicada, trg_mov_orden numera los renglones (ADR 0006).
    repository.cambiar_estado(session, movimiento_id, estado)
    session.commit()
    return detalle(session, repository.buscar_cabecera(session, movimiento_id))


def listar_devueltas(
    session: Session, usuario: UsuarioPublic
) -> list[MovimientoPublic]:
    return [
        detalle(session, cabecera)
        for cabecera in repository.listar_devueltas(session, usuario.unidad.id)
    ]


def validar_acta_devuelta(
    session: Session, usuario: UsuarioPublic, movimiento_id: int, sin_permiso: str
) -> None:
    cabecera = repository.buscar_cabecera(session, movimiento_id)
    if cabecera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="El movimiento no existe"
        )
    if cabecera["unidad_origen_id"] != usuario.unidad.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=sin_permiso)
    if cabecera["estado"] != "DEVUELTO":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="El acta no está devuelta"
        )


def corregir_entrega(
    session: Session,
    usuario: UsuarioPublic,
    movimiento_id: int,
    entrega: EntregaCreate,
) -> MovimientoPublic:
    # Se bloquea el acta antes que sus bienes, como recibir y desistir: así dos
    # operaciones sobre la misma acta no se cruzan en un deadlock (ADR 0001).
    bloquear_movimiento(session, movimiento_id)
    ids = set(entrega.bienes)
    actuales = {
        renglon["bien_id"]
        for renglon in repository.listar_renglones(session, movimiento_id)
    }
    # Se bloquean los que entran y los que salen antes de leer el estado: otra
    # operación sobre el acta espera acá y, con READ COMMITTED, al seguir ve el
    # acta reenviada o rechazada (ADR 0001).
    bloqueados = repository.bloquear_bienes(session, sorted(ids | actuales))
    validar_acta_devuelta(
        session, usuario, movimiento_id, "Solo la unidad de origen corrige el acta"
    )
    bienes = [bien for bien in bloqueados if bien.id in ids]
    validar_entrega(session, usuario.unidad.id, entrega, bienes, movimiento_id)
    repository.quitar_renglones(session, movimiento_id)
    for bien in bienes:
        repository.insertar_renglon(session, movimiento_id, bien.id, bien.ubicacion_id)
    # El original no se modifica: la corrección es una versión nueva (ADR 0010).
    repository.insertar_rectificacion(
        session,
        movimiento_id=movimiento_id,
        fecha_hecho=entrega.fecha_hecho,
        numero_acta=entrega.numero_acta,
        descripcion=entrega.descripcion,
        motivo=repository.listar_recepciones(session, movimiento_id)[-1]["motivo"],
        usuario_id=usuario.id,
    )
    repository.reenviar_entrega(session, movimiento_id, entrega.unidad_destino_id)
    session.commit()
    return detalle(session, repository.buscar_cabecera(session, movimiento_id))


def desistir_de_la_entrega(
    session: Session,
    usuario: UsuarioPublic,
    movimiento_id: int,
    desistimiento: DesistimientoCreate,
) -> MovimientoPublic:
    # Se bloquean el acta y sus bienes antes de leer el estado: otra operación
    # sobre el acta espera acá y, con READ COMMITTED, al seguir ve el acta
    # reenviada (ADR 0001).
    bloquear_movimiento(session, movimiento_id)
    repository.bloquear_bienes_del_movimiento(session, movimiento_id)
    validar_acta_devuelta(
        session, usuario, movimiento_id, "Solo la unidad de origen desiste del acta"
    )
    repository.insertar_recepcion(
        session,
        movimiento_id=movimiento_id,
        resultado="RECHAZADO",
        motivo=desistimiento.motivo,
        usuario_id=usuario.id,
    )
    repository.cambiar_estado(session, movimiento_id, "RECHAZADO")
    session.commit()
    return detalle(session, repository.buscar_cabecera(session, movimiento_id))


def listar_observados(
    session: Session, usuario: UsuarioPublic
) -> list[MovimientoPublic]:
    return [
        detalle(session, cabecera)
        for cabecera in repository.listar_observados(session, usuario.unidad.id)
    ]


def rectificar_movimiento(
    session: Session,
    usuario: UsuarioPublic,
    movimiento_id: int,
    rectificacion: RectificacionCreate,
) -> MovimientoPublic:
    # Se bloquea antes de leer el estado: otra corrección espera acá y, con
    # READ COMMITTED, al seguir numera su versión después de esta (ADR 0001).
    movimiento = bloquear_movimiento(session, movimiento_id)
    if movimiento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="El movimiento no existe"
        )
    if movimiento["unidad_registrante_id"] != usuario.unidad.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo la unidad que registró el movimiento lo corrige",
        )
    if movimiento["estado"] != "APLICADO":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se corrigen movimientos aplicados",
        )
    # El original no se modifica: la corrección es una versión nueva (RN-07).
    repository.insertar_rectificacion(
        session,
        movimiento_id=movimiento_id,
        fecha_hecho=rectificacion.fecha_hecho,
        numero_acta=rectificacion.numero_acta,
        descripcion=rectificacion.descripcion,
        motivo=rectificacion.motivo,
        usuario_id=usuario.id,
    )
    # Lo que registra Dirección no se revisa (RN-06).
    if movimiento["estado_revision"] != "NO_APLICA":
        cambiar_estado_revision(session, movimiento_id, "PENDIENTE")
    session.commit()
    return detalle(session, repository.buscar_cabecera(session, movimiento_id))


def detalle(session: Session, cabecera: RowMapping) -> MovimientoPublic:
    return MovimientoPublic(
        **cabecera,
        unidad_origen=unidad_publica(session, cabecera["unidad_origen_id"]),
        unidad_destino=unidad_publica(session, cabecera["unidad_destino_id"]),
        oficial_origen=oficial_publico(session, cabecera["oficial_origen_id"]),
        oficial_destino=oficial_publico(session, cabecera["oficial_destino_id"]),
        bienes=[
            RenglonPublic.model_validate(renglon)
            for renglon in repository.listar_renglones(session, cabecera["id"])
        ],
        versiones=[
            VersionPublic.model_validate(version)
            for version in repository.listar_versiones(session, cabecera["id"])
        ],
        revisiones=[
            RevisionPublic.model_validate(revision)
            for revision in listar_revisiones(session, cabecera["id"])
        ],
        recepciones=[
            RecepcionPublic(
                **recepcion,
                bienes_con_novedad=[
                    NovedadPublic.model_validate(novedad)
                    for novedad in repository.listar_novedades(session, recepcion["id"])
                ],
            )
            for recepcion in repository.listar_recepciones(session, cabecera["id"])
        ],
    )


def unidad_publica(session: Session, unidad_id: int | None) -> UnidadPublic | None:
    unidad = session.get(Unidad, unidad_id) if unidad_id else None
    return UnidadPublic.model_validate(unidad) if unidad else None
