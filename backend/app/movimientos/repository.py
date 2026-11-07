from sqlalchemy import Row, RowMapping, bindparam
from sqlmodel import Session, text

BLOQUEAR_BIENES = text(
    "SELECT id, tipo_bien, unidad_id, oficial_id, ubicacion_id, de_baja, "
    "estado_operativo "
    "FROM bien WHERE id IN :bienes ORDER BY id FOR UPDATE"
).bindparams(bindparam("bienes", expanding=True))

ALGUNO_CON_MOVIMIENTO_PENDIENTE = text(
    "SELECT EXISTS (SELECT 1 FROM movimiento_bien mb "
    "JOIN movimiento m ON m.id = mb.movimiento_id "
    "WHERE mb.bien_id IN :bienes AND m.estado IN ('PENDIENTE', 'DEVUELTO') "
    "AND m.id <> :excluir)"
).bindparams(bindparam("bienes", expanding=True))

INSERTAR_ENTREGA = text(
    "INSERT INTO movimiento (tipo, estado, estado_revision, numero_acta, "
    "fecha_hecho, descripcion, usuario_id, unidad_registrante_id, "
    "unidad_origen_id, unidad_destino_id) "
    "VALUES ('ENTREGA', 'PENDIENTE', :estado_revision, :numero_acta, "
    ":fecha_hecho, :descripcion, :usuario_id, :unidad_id, :unidad_id, "
    ":unidad_destino_id)"
)

INSERTAR_DOTACION = text(
    "INSERT INTO movimiento (tipo, estado, estado_revision, numero_acta, "
    "fecha_hecho, descripcion, usuario_id, unidad_registrante_id, "
    "unidad_origen_id, unidad_destino_id, oficial_destino_id) "
    "VALUES ('ENTREGA', 'APLICADO', :estado_revision, :numero_acta, "
    ":fecha_hecho, :descripcion, :usuario_id, :unidad_id, :unidad_id, "
    ":unidad_id, :oficial_id)"
)

INSERTAR_RENGLON = text(
    "INSERT INTO movimiento_bien (movimiento_id, bien_id, ubicacion_origen_id) "
    "VALUES (:movimiento_id, :bien_id, :ubicacion_id)"
)

CABECERA = text(
    "SELECT v.id, v.tipo, v.estado, v.estado_revision, v.numero_acta, "
    "v.fecha_hecho, v.descripcion, v.unidad_origen_id, v.unidad_destino_id, "
    "v.oficial_origen_id, v.oficial_destino_id, "
    "u.nombre_usuario AS usuario, v.fecha_carga, v.version_vigente, "
    "r.motivo AS motivo_rechazo "
    "FROM v_movimiento_vigente v JOIN usuario u ON u.id = v.usuario_id "
    "LEFT JOIN recepcion r ON r.movimiento_id = v.id AND r.resultado = 'RECHAZADO' "
    "WHERE v.id = :id"
)

POR_RECIBIR = text(
    "SELECT v.id, v.tipo, v.estado, v.estado_revision, v.numero_acta, "
    "v.fecha_hecho, v.descripcion, v.unidad_origen_id, v.unidad_destino_id, "
    "v.oficial_origen_id, v.oficial_destino_id, "
    "u.nombre_usuario AS usuario, v.fecha_carga, v.version_vigente "
    "FROM v_movimiento_vigente v JOIN usuario u ON u.id = v.usuario_id "
    "WHERE v.tipo = 'ENTREGA' AND v.estado = 'PENDIENTE' "
    "AND v.unidad_destino_id = :unidad_id ORDER BY v.id"
)

DEVUELTAS = text(
    "SELECT v.id, v.tipo, v.estado, v.estado_revision, v.numero_acta, "
    "v.fecha_hecho, v.descripcion, v.unidad_origen_id, v.unidad_destino_id, "
    "v.oficial_origen_id, v.oficial_destino_id, "
    "u.nombre_usuario AS usuario, v.fecha_carga, v.version_vigente "
    "FROM v_movimiento_vigente v JOIN usuario u ON u.id = v.usuario_id "
    "WHERE v.estado = 'DEVUELTO' AND v.unidad_origen_id = :unidad_id ORDER BY v.id"
)

OBSERVADOS = text(
    "SELECT v.id, v.tipo, v.estado, v.estado_revision, v.numero_acta, "
    "v.fecha_hecho, v.descripcion, v.unidad_origen_id, v.unidad_destino_id, "
    "v.oficial_origen_id, v.oficial_destino_id, "
    "u.nombre_usuario AS usuario, v.fecha_carga, v.version_vigente "
    "FROM v_movimiento_vigente v JOIN usuario u ON u.id = v.usuario_id "
    "WHERE v.estado = 'APLICADO' AND v.estado_revision = 'OBSERVADO' "
    "AND v.unidad_registrante_id = :unidad_id ORDER BY v.id"
)

VERSIONES = text(
    "SELECT 0 AS version, m.fecha_hecho, m.numero_acta, m.descripcion, "
    "NULL AS motivo, u.nombre_usuario AS usuario, m.fecha_carga AS fecha "
    "FROM movimiento m JOIN usuario u ON u.id = m.usuario_id WHERE m.id = :id "
    "UNION ALL "
    "SELECT r.version, r.fecha_hecho, r.numero_acta, r.descripcion, r.motivo, "
    "u.nombre_usuario, r.fecha "
    "FROM rectificacion r JOIN usuario u ON u.id = r.usuario_id "
    "WHERE r.movimiento_id = :id ORDER BY version"
)

INSERTAR_RECTIFICACION = text(
    "INSERT INTO rectificacion (movimiento_id, version, fecha_hecho, numero_acta, "
    "descripcion, motivo, usuario_id) "
    "SELECT :movimiento_id, COALESCE(MAX(version), 0) + 1, :fecha_hecho, "
    ":numero_acta, :descripcion, :motivo, :usuario_id "
    "FROM rectificacion WHERE movimiento_id = :movimiento_id"
)

BLOQUEAR_BIENES_DEL_MOVIMIENTO = text(
    "SELECT b.id FROM movimiento_bien mb JOIN bien b ON b.id = mb.bien_id "
    "WHERE mb.movimiento_id = :id ORDER BY b.id FOR UPDATE"
)

UBICAR_RENGLON = text(
    "UPDATE movimiento_bien SET ubicacion_destino_id = :ubicacion_id "
    "WHERE movimiento_id = :movimiento_id AND bien_id = :bien_id"
)

MOVER_BIENES = text(
    "UPDATE bien b JOIN movimiento_bien mb ON mb.bien_id = b.id "
    "JOIN movimiento m ON m.id = mb.movimiento_id "
    "SET b.unidad_id = m.unidad_destino_id, b.ubicacion_id = mb.ubicacion_destino_id "
    "WHERE mb.movimiento_id = :id"
)

ASIGNAR_BIENES = text(
    "UPDATE bien b JOIN movimiento_bien mb ON mb.bien_id = b.id "
    "JOIN movimiento m ON m.id = mb.movimiento_id "
    "SET b.oficial_id = m.oficial_destino_id, b.ubicacion_id = NULL "
    "WHERE mb.movimiento_id = :id"
)

INSERTAR_RECEPCION = text(
    "INSERT INTO recepcion (movimiento_id, resultado, motivo, usuario_id) "
    "VALUES (:movimiento_id, :resultado, :motivo, :usuario_id)"
)

INSERTAR_NOVEDAD = text(
    "INSERT INTO recepcion_novedad (recepcion_id, bien_id) "
    "VALUES (:recepcion_id, :bien_id)"
)

RECEPCIONES = text(
    "SELECT r.id, r.resultado, r.motivo, u.nombre_usuario AS usuario, r.fecha "
    "FROM recepcion r JOIN usuario u ON u.id = r.usuario_id "
    "WHERE r.movimiento_id = :id ORDER BY r.id"
)

NOVEDADES = text(
    "SELECT rn.bien_id, COALESCE(b.numero_serie, ml.patente) AS identificacion "
    "FROM recepcion_novedad rn JOIN bien b ON b.id = rn.bien_id "
    "LEFT JOIN movil ml ON ml.bien_id = b.id "
    "WHERE rn.recepcion_id = :id ORDER BY rn.bien_id"
)

QUITAR_RENGLONES = text("DELETE FROM movimiento_bien WHERE movimiento_id = :id")

REENVIAR_ENTREGA = text(
    "UPDATE movimiento SET estado = 'PENDIENTE', "
    "unidad_destino_id = :unidad_destino_id WHERE id = :id"
)

CAMBIAR_ESTADO = text("UPDATE movimiento SET estado = :estado WHERE id = :id")

UNIDADES_ACTUALES_DE_LOS_BIENES = text(
    "SELECT DISTINCT b.unidad_id FROM movimiento_bien mb "
    "JOIN bien b ON b.id = mb.bien_id WHERE mb.movimiento_id = :id"
)

RENGLONES = text(
    "SELECT mb.bien_id, b.tipo_bien, "
    "COALESCE(b.numero_serie, ml.patente) AS identificacion, b.marca, b.modelo, "
    "b.estado_operativo, uo.nombre AS ubicacion_origen, "
    "ud.nombre AS ubicacion_destino "
    "FROM movimiento_bien mb "
    "JOIN bien b ON b.id = mb.bien_id "
    "LEFT JOIN movil ml ON ml.bien_id = b.id "
    "LEFT JOIN ubicacion uo ON uo.id = mb.ubicacion_origen_id "
    "LEFT JOIN ubicacion ud ON ud.id = mb.ubicacion_destino_id "
    "WHERE mb.movimiento_id = :id ORDER BY mb.bien_id"
)


def bloquear_bienes(session: Session, bienes: list[int]) -> list[Row]:
    return list(session.exec(BLOQUEAR_BIENES, params={"bienes": bienes}))


def alguno_con_movimiento_pendiente(
    session: Session, bienes: list[int], excluir: int = 0
) -> bool:
    return bool(
        session.exec(
            ALGUNO_CON_MOVIMIENTO_PENDIENTE,
            params={"bienes": bienes, "excluir": excluir},
        ).scalar_one()
    )


def insertar_entrega(session: Session, **valores) -> int:
    return session.exec(INSERTAR_ENTREGA, params=valores).lastrowid


def insertar_dotacion(session: Session, **valores) -> int:
    return session.exec(INSERTAR_DOTACION, params=valores).lastrowid


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


def unidades_actuales_de_los_bienes(session: Session, movimiento_id: int) -> set[int]:
    return set(
        session.exec(
            UNIDADES_ACTUALES_DE_LOS_BIENES, params={"id": movimiento_id}
        ).scalars()
    )


def listar_por_recibir(session: Session, unidad_id: int) -> list[RowMapping]:
    return list(session.exec(POR_RECIBIR, params={"unidad_id": unidad_id}).mappings())


def listar_devueltas(session: Session, unidad_id: int) -> list[RowMapping]:
    return list(session.exec(DEVUELTAS, params={"unidad_id": unidad_id}).mappings())


def listar_observados(session: Session, unidad_id: int) -> list[RowMapping]:
    return list(session.exec(OBSERVADOS, params={"unidad_id": unidad_id}).mappings())


def listar_versiones(session: Session, movimiento_id: int) -> list[RowMapping]:
    return list(session.exec(VERSIONES, params={"id": movimiento_id}).mappings())


def insertar_rectificacion(session: Session, **valores) -> None:
    session.exec(INSERTAR_RECTIFICACION, params=valores)


def bloquear_bienes_del_movimiento(session: Session, movimiento_id: int) -> list[int]:
    return list(
        session.exec(
            BLOQUEAR_BIENES_DEL_MOVIMIENTO, params={"id": movimiento_id}
        ).scalars()
    )


def ubicar_renglon(
    session: Session, movimiento_id: int, bien_id: int, ubicacion_id: int
) -> None:
    session.exec(
        UBICAR_RENGLON,
        params={
            "movimiento_id": movimiento_id,
            "bien_id": bien_id,
            "ubicacion_id": ubicacion_id,
        },
    )


def mover_bienes(session: Session, movimiento_id: int) -> None:
    session.exec(MOVER_BIENES, params={"id": movimiento_id})


def asignar_bienes(session: Session, movimiento_id: int) -> None:
    session.exec(ASIGNAR_BIENES, params={"id": movimiento_id})


def insertar_recepcion(session: Session, **valores) -> int:
    return session.exec(INSERTAR_RECEPCION, params=valores).lastrowid


def insertar_novedad(session: Session, recepcion_id: int, bien_id: int) -> None:
    session.exec(
        INSERTAR_NOVEDAD, params={"recepcion_id": recepcion_id, "bien_id": bien_id}
    )


def listar_recepciones(session: Session, movimiento_id: int) -> list[RowMapping]:
    return list(session.exec(RECEPCIONES, params={"id": movimiento_id}).mappings())


def listar_novedades(session: Session, recepcion_id: int) -> list[RowMapping]:
    return list(session.exec(NOVEDADES, params={"id": recepcion_id}).mappings())


def quitar_renglones(session: Session, movimiento_id: int) -> None:
    session.exec(QUITAR_RENGLONES, params={"id": movimiento_id})


def reenviar_entrega(
    session: Session, movimiento_id: int, unidad_destino_id: int
) -> None:
    session.exec(
        REENVIAR_ENTREGA,
        params={"id": movimiento_id, "unidad_destino_id": unidad_destino_id},
    )


def cambiar_estado(session: Session, movimiento_id: int, estado: str) -> None:
    session.exec(CAMBIAR_ESTADO, params={"id": movimiento_id, "estado": estado})
