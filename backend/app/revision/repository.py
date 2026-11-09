from sqlalchemy import RowMapping
from sqlmodel import Session, text

BANDEJA = text(
    "SELECT b.registro, b.registro_id, b.evento, b.fecha, "
    "un.nombre AS unidad_registrante, us.nombre_usuario AS usuario, b.detalle, "
    "b.version_vigente AS version, m.numero_acta, uo.nombre AS unidad_origen, "
    "ud.nombre AS unidad_destino, m.oficial_origen_id, m.oficial_destino_id, "
    "COALESCE(bc.numero_serie, mc.patente) AS bien_identificacion, c.estado_nuevo "
    "FROM v_bandeja_revision b "
    "JOIN unidad un ON un.id = b.unidad_registrante_id "
    "JOIN usuario us ON us.id = b.usuario_id "
    "LEFT JOIN v_movimiento_vigente m "
    "ON b.registro = 'MOVIMIENTO' AND m.id = b.registro_id "
    "LEFT JOIN unidad uo ON uo.id = m.unidad_origen_id "
    "LEFT JOIN unidad ud ON ud.id = m.unidad_destino_id "
    "LEFT JOIN v_cambio_estado_vigente c "
    "ON b.registro = 'CAMBIO_ESTADO' AND c.id = b.registro_id "
    "LEFT JOIN bien bc ON bc.id = c.bien_id "
    "LEFT JOIN movil mc ON mc.bien_id = bc.id "
    "WHERE b.unidad_revisora_id = :unidad_id "
    "ORDER BY b.fecha, b.registro, b.registro_id"
)

BLOQUEAR_MOVIMIENTO = text(
    "SELECT estado, estado_revision, unidad_registrante_id "
    "FROM movimiento WHERE id = :id FOR UPDATE"
)

INSERTAR_REVISION = text(
    "INSERT INTO revision (movimiento_id, cambio_estado_id, resultado, "
    "motivo_observacion, version_revisada, usuario_id) "
    "VALUES (:movimiento_id, :cambio_estado_id, :resultado, :motivo_observacion, "
    ":version_revisada, :usuario_id)"
)

CAMBIAR_ESTADO_REVISION = text(
    "UPDATE movimiento SET estado_revision = :estado_revision WHERE id = :id"
)

REVISION = text(
    "SELECT r.resultado, r.version_revisada, r.motivo_observacion, "
    "u.nombre_usuario AS usuario, r.fecha "
    "FROM revision r JOIN usuario u ON u.id = r.usuario_id WHERE r.id = :id"
)

REVISIONES_DEL_MOVIMIENTO = text(
    "SELECT r.resultado, r.version_revisada, r.motivo_observacion, "
    "u.nombre_usuario AS usuario, r.fecha "
    "FROM revision r JOIN usuario u ON u.id = r.usuario_id "
    "WHERE r.movimiento_id = :id ORDER BY r.id"
)


def listar_bandeja(session: Session, unidad_id: int) -> list[RowMapping]:
    return list(session.exec(BANDEJA, params={"unidad_id": unidad_id}).mappings())


def bloquear_movimiento(session: Session, movimiento_id: int) -> RowMapping | None:
    return (
        session.exec(BLOQUEAR_MOVIMIENTO, params={"id": movimiento_id})
        .mappings()
        .first()
    )


def insertar_revision(session: Session, **valores) -> int:
    return session.exec(INSERTAR_REVISION, params=valores).lastrowid


def cambiar_estado_revision(
    session: Session, movimiento_id: int, estado_revision: str
) -> None:
    session.exec(
        CAMBIAR_ESTADO_REVISION,
        params={"id": movimiento_id, "estado_revision": estado_revision},
    )


def buscar_revision(session: Session, revision_id: int) -> RowMapping:
    return session.exec(REVISION, params={"id": revision_id}).mappings().one()


def listar_revisiones(session: Session, movimiento_id: int) -> list[RowMapping]:
    return list(
        session.exec(REVISIONES_DEL_MOVIMIENTO, params={"id": movimiento_id}).mappings()
    )
