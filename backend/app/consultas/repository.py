from sqlalchemy import RowMapping, bindparam
from sqlmodel import Session, text

INVENTARIO = text(
    "SELECT * FROM v_inventario_unidad "
    "WHERE unidad_id IN :unidades "
    "AND (:tipo_bien IS NULL OR tipo_bien = :tipo_bien) "
    "ORDER BY unidad_id, tipo_bien, identificacion"
).bindparams(bindparam("unidades", expanding=True))

BIEN = text(
    "SELECT b.id, b.tipo_bien, COALESCE(b.numero_serie, m.patente) AS identificacion, "
    "b.marca, b.modelo, b.unidad_id, u.nombre AS unidad "
    "FROM bien b JOIN unidad u ON u.id = b.unidad_id "
    "LEFT JOIN movil m ON m.bien_id = b.id WHERE b.id = :id"
)

# Las actas rechazadas o pendientes no tienen orden (ADR 0006): van al final
# por fecha de carga.
HISTORIAL = text(
    "SELECT h.registro, h.registro_id, h.orden, h.evento, h.fecha, h.numero_acta, "
    "h.estado, h.estado_revision, h.detalle, "
    "NULLIF(CONCAT_WS(', ', uo.nombre, CONCAT(oo.apellido, ', ', oo.nombre), "
    "ubo.nombre), '') AS origen, "
    "NULLIF(CONCAT_WS(', ', ud.nombre, CONCAT(od.apellido, ', ', od.nombre), "
    "ubd.nombre), '') AS destino "
    "FROM v_historial_bien h "
    "LEFT JOIN unidad uo ON uo.id = h.unidad_origen_id "
    "LEFT JOIN oficial oo ON oo.id = h.oficial_origen_id "
    "LEFT JOIN ubicacion ubo ON ubo.id = h.ubicacion_origen_id "
    "LEFT JOIN unidad ud ON ud.id = h.unidad_destino_id "
    "LEFT JOIN oficial od ON od.id = h.oficial_destino_id "
    "LEFT JOIN ubicacion ubd ON ubd.id = h.ubicacion_destino_id "
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
