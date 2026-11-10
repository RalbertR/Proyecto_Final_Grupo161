from sqlalchemy import RowMapping, bindparam
from sqlmodel import Session, text

INVENTARIO = text(
    "SELECT v.*, b.oficial_id FROM v_inventario_unidad v "
    "JOIN bien b ON b.id = v.bien_id "
    "WHERE v.unidad_id IN :unidades "
    "AND (:tipo_bien IS NULL OR v.tipo_bien = :tipo_bien) "
    "ORDER BY v.unidad_id, v.tipo_bien, v.identificacion"
).bindparams(bindparam("unidades", expanding=True))

BIEN = text(
    "SELECT b.id, b.tipo_bien, COALESCE(b.numero_serie, m.patente) AS identificacion, "
    "b.marca, b.modelo, b.unidad_id, u.nombre AS unidad, b.estado_operativo, b.de_baja, "
    "CASE WHEN b.oficial_id IS NOT NULL THEN 'DOTACION' ELSE 'DEPOSITO' END "
    "AS tenencia, ub.nombre AS ubicacion, o.legajo AS oficial_legajo, "
    "CONCAT(o.apellido, ', ', o.nombre) AS oficial, "
    "EXISTS (SELECT 1 FROM movimiento_bien mb "
    "JOIN movimiento mv ON mv.id = mb.movimiento_id "
    "WHERE mb.bien_id = b.id AND mv.estado IN ('PENDIENTE', 'DEVUELTO')) "
    "AS con_movimiento_pendiente "
    "FROM bien b JOIN unidad u ON u.id = b.unidad_id "
    "LEFT JOIN movil m ON m.bien_id = b.id "
    "LEFT JOIN ubicacion ub ON ub.id = b.ubicacion_id "
    "LEFT JOIN oficial o ON o.id = b.oficial_id WHERE b.id = :id"
)

# Las actas rechazadas o pendientes no tienen orden (ADR 0006): van al final
# por fecha de carga.
HISTORIAL = text(
    "SELECT h.registro, h.registro_id, h.orden, h.evento, h.fecha, h.numero_acta, "
    "h.estado, h.estado_revision, h.detalle, h.estado_operativo_nuevo, "
    "h.oficial_origen_id, h.oficial_destino_id, "
    "ce.documento_id IS NOT NULL AS tiene_informe, "
    "CASE WHEN h.estado = 'APLICADO' THEN COALESCE(ud.nombre, uo.nombre) "
    "ELSE COALESCE(uo.nombre, ud.nombre) END AS unidad_duena, "
    "NULLIF(CONCAT_WS(', ', uo.nombre, CONCAT(oo.apellido, ', ', oo.nombre), "
    "ubo.nombre), '') AS origen, "
    "NULLIF(CONCAT_WS(', ', ud.nombre, CONCAT(od.apellido, ', ', od.nombre), "
    "ubd.nombre), '') AS destino, "
    "uo.nombre AS unidad_origen, ubo.nombre AS ubicacion_origen, "
    "CONCAT(oo.apellido, ', ', oo.nombre) AS oficial_origen, "
    "ubd.nombre AS ubicacion_destino, "
    "CONCAT(od.apellido, ', ', od.nombre) AS oficial_destino "
    "FROM v_historial_bien h "
    "LEFT JOIN unidad uo ON uo.id = h.unidad_origen_id "
    "LEFT JOIN oficial oo ON oo.id = h.oficial_origen_id "
    "LEFT JOIN ubicacion ubo ON ubo.id = h.ubicacion_origen_id "
    "LEFT JOIN unidad ud ON ud.id = h.unidad_destino_id "
    "LEFT JOIN oficial od ON od.id = h.oficial_destino_id "
    "LEFT JOIN ubicacion ubd ON ubd.id = h.ubicacion_destino_id "
    "LEFT JOIN v_cambio_estado_vigente ce "
    "ON h.registro = 'CAMBIO_ESTADO' AND ce.id = h.registro_id "
    "WHERE h.bien_id = :id "
    "ORDER BY h.orden IS NULL, h.orden, h.fecha_carga, h.registro, h.registro_id"
)


def listar_inventario(
    session: Session, unidades: list[int], tipo_bien: str | None
) -> list[RowMapping]:
    return list(
        session.exec(
            INVENTARIO, params={"unidades": unidades, "tipo_bien": tipo_bien}
        ).mappings()
    )


def buscar_bien(session: Session, bien_id: int) -> RowMapping | None:
    return session.exec(BIEN, params={"id": bien_id}).mappings().first()


def listar_historial(session: Session, bien_id: int) -> list[RowMapping]:
    return list(session.exec(HISTORIAL, params={"id": bien_id}).mappings())
