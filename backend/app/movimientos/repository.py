from sqlalchemy import Row, RowMapping, bindparam
from sqlmodel import Session, text

BLOQUEAR_BIENES = text(
    "SELECT id, tipo_bien, unidad_id, oficial_id, ubicacion_id, de_baja "
    "FROM bien WHERE id IN :bienes ORDER BY id FOR UPDATE"
).bindparams(bindparam("bienes", expanding=True))

ALGUNO_CON_MOVIMIENTO_PENDIENTE = text(
    "SELECT EXISTS (SELECT 1 FROM movimiento_bien mb "
    "JOIN movimiento m ON m.id = mb.movimiento_id "
    "WHERE mb.bien_id IN :bienes AND m.estado = 'PENDIENTE')"
).bindparams(bindparam("bienes", expanding=True))

INSERTAR_ENTREGA = text(
    "INSERT INTO movimiento (tipo, estado, estado_revision, numero_acta, "
    "fecha_hecho, descripcion, usuario_id, unidad_registrante_id, "
    "unidad_origen_id, unidad_destino_id) "
    "VALUES ('ENTREGA', 'PENDIENTE', :estado_revision, :numero_acta, "
    ":fecha_hecho, :descripcion, :usuario_id, :unidad_id, :unidad_id, "
    ":unidad_destino_id)"
)

INSERTAR_RENGLON = text(
    "INSERT INTO movimiento_bien (movimiento_id, bien_id, ubicacion_origen_id) "
    "VALUES (:movimiento_id, :bien_id, :ubicacion_id)"
)

CABECERA = text(
    "SELECT v.id, v.tipo, v.estado, v.estado_revision, v.numero_acta, "
    "v.fecha_hecho, v.descripcion, v.unidad_origen_id, v.unidad_destino_id, "
    "u.nombre_usuario AS usuario, v.fecha_carga "
    "FROM v_movimiento_vigente v JOIN usuario u ON u.id = v.usuario_id "
    "WHERE v.id = :id"
)

RENGLONES = text(
    "SELECT mb.bien_id, b.tipo_bien, "
    "COALESCE(b.numero_serie, ml.patente) AS identificacion, b.marca, b.modelo, "
    "uo.nombre AS ubicacion_origen, ud.nombre AS ubicacion_destino "
    "FROM movimiento_bien mb "
    "JOIN bien b ON b.id = mb.bien_id "
    "LEFT JOIN movil ml ON ml.bien_id = b.id "
    "LEFT JOIN ubicacion uo ON uo.id = mb.ubicacion_origen_id "
    "LEFT JOIN ubicacion ud ON ud.id = mb.ubicacion_destino_id "
    "WHERE mb.movimiento_id = :id ORDER BY mb.bien_id"
)


def bloquear_bienes(session: Session, bienes: list[int]) -> list[Row]:
    return list(session.exec(BLOQUEAR_BIENES, params={"bienes": bienes}))


def alguno_con_movimiento_pendiente(session: Session, bienes: list[int]) -> bool:
    return bool(
        session.exec(
            ALGUNO_CON_MOVIMIENTO_PENDIENTE, params={"bienes": bienes}
        ).scalar_one()
    )


def insertar_entrega(session: Session, **valores) -> int:
    return session.exec(INSERTAR_ENTREGA, params=valores).lastrowid


def insertar_renglon(
    session: Session, movimiento_id: int, bien_id: int, ubicacion_id: int
) -> None:
    session.exec(
        INSERTAR_RENGLON,
        params={
            "movimiento_id": movimiento_id,
            "bien_id": bien_id,
            "ubicacion_id": ubicacion_id,
        },
    )


def buscar_cabecera(session: Session, movimiento_id: int) -> RowMapping | None:
    return session.exec(CABECERA, params={"id": movimiento_id}).mappings().first()


def listar_renglones(session: Session, movimiento_id: int) -> list[RowMapping]:
    return list(session.exec(RENGLONES, params={"id": movimiento_id}).mappings())
