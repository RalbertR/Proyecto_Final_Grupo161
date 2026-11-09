from sqlalchemy import RowMapping
from sqlmodel import Session, text

BLOQUEAR_BIEN = text(
    "SELECT id, unidad_id, estado_operativo, de_baja FROM bien WHERE id = :id FOR UPDATE"
)

CON_MOVIMIENTO_PENDIENTE = text(
    "SELECT EXISTS (SELECT 1 FROM movimiento_bien mb "
    "JOIN movimiento mv ON mv.id = mb.movimiento_id "
    "WHERE mb.bien_id = :id AND mv.estado IN ('PENDIENTE', 'DEVUELTO'))"
)

INSERTAR_CAMBIO = text(
    "INSERT INTO cambio_estado_operativo (bien_id, estado_anterior, estado_nuevo, "
    "observaciones, documento_id, estado_revision, usuario_id, unidad_registrante_id) "
    "VALUES (:bien_id, :estado_anterior, :estado_nuevo, :observaciones, "
    ":documento_id, :estado_revision, :usuario_id, :unidad_registrante_id)"
)

CAMBIAR_ESTADO_BIEN = text("UPDATE bien SET estado_operativo = :estado WHERE id = :id")

CAMBIO = text(
    "SELECT c.id, c.bien_id, c.estado, c.estado_anterior, c.estado_nuevo, "
    "c.observaciones, c.documento_id, c.version_vigente, c.estado_revision, "
    "c.unidad_registrante_id, c.fecha, un.nombre AS unidad_registrante, "
    "un.unidad_superior_id, us.nombre_usuario AS usuario, "
    "b.unidad_id AS unidad_bien_id, b.tipo_bien, b.marca, b.modelo, "
    "COALESCE(b.numero_serie, m.patente) AS identificacion, "
    "d.nombre_original, d.tamano_bytes, d.ruta_almacenamiento "
    "FROM v_cambio_estado_vigente c "
    "JOIN bien b ON b.id = c.bien_id "
    "LEFT JOIN movil m ON m.bien_id = b.id "
    "JOIN unidad un ON un.id = c.unidad_registrante_id "
    "JOIN usuario us ON us.id = c.usuario_id "
    "LEFT JOIN documento d ON d.id = c.documento_id "
    "WHERE c.id = :id"
)

BLOQUEAR_CAMBIO = text(
    "SELECT id FROM cambio_estado_operativo WHERE id = :id FOR UPDATE"
)

CAMBIO_VIGENTE = text(
    "SELECT estado, estado_revision, estado_nuevo, documento_id, "
    "unidad_registrante_id, version_vigente "
    "FROM v_cambio_estado_vigente WHERE id = :id"
)

CAMBIAR_ESTADO_REVISION = text(
    "UPDATE cambio_estado_operativo SET estado_revision = :estado_revision "
    "WHERE id = :id"
)

REVISIONES_DEL_CAMBIO = text(
    "SELECT r.resultado, r.version_revisada, r.motivo_observacion, "
    "u.nombre_usuario AS usuario, r.fecha "
    "FROM revision r JOIN usuario u ON u.id = r.usuario_id "
    "WHERE r.cambio_estado_id = :id ORDER BY r.id"
)

RECTIFICACIONES_DEL_CAMBIO = text(
    "SELECT r.version, r.motivo, u.nombre_usuario AS usuario, r.fecha "
    "FROM rectificacion_cambio_estado r JOIN usuario u ON u.id = r.usuario_id "
    "WHERE r.cambio_estado_id = :id ORDER BY r.version"
)


def bloquear_bien(session: Session, bien_id: int) -> RowMapping | None:
    return session.exec(BLOQUEAR_BIEN, params={"id": bien_id}).mappings().first()


def con_movimiento_pendiente(session: Session, bien_id: int) -> bool:
    return bool(session.exec(CON_MOVIMIENTO_PENDIENTE, params={"id": bien_id}).scalar())


def insertar_cambio(session: Session, **valores) -> int:
    return session.exec(INSERTAR_CAMBIO, params=valores).lastrowid


def cambiar_estado_bien(session: Session, bien_id: int, estado: str) -> None:
    session.exec(CAMBIAR_ESTADO_BIEN, params={"id": bien_id, "estado": estado})


def buscar_cambio(session: Session, cambio_id: int) -> RowMapping | None:
    return session.exec(CAMBIO, params={"id": cambio_id}).mappings().first()


def listar_revisiones(session: Session, cambio_id: int) -> list[RowMapping]:
    return list(
        session.exec(REVISIONES_DEL_CAMBIO, params={"id": cambio_id}).mappings()
    )


def listar_rectificaciones(session: Session, cambio_id: int) -> list[RowMapping]:
    return list(
        session.exec(RECTIFICACIONES_DEL_CAMBIO, params={"id": cambio_id}).mappings()
    )


def bloquear_cambio(session: Session, cambio_id: int) -> RowMapping | None:
    if session.exec(BLOQUEAR_CAMBIO, params={"id": cambio_id}).first() is None:
        return None
    return session.exec(CAMBIO_VIGENTE, params={"id": cambio_id}).mappings().one()


def cambiar_estado_revision(
    session: Session, cambio_id: int, estado_revision: str
) -> None:
    session.exec(
        CAMBIAR_ESTADO_REVISION,
        params={"id": cambio_id, "estado_revision": estado_revision},
    )
