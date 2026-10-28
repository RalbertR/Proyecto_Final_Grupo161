from sqlalchemy import RowMapping, bindparam
from sqlmodel import Session, text

INVENTARIO = text(
    "SELECT * FROM v_inventario_unidad "
    "WHERE unidad_id IN :unidades "
    "AND (:tipo_bien IS NULL OR tipo_bien = :tipo_bien) "
    "ORDER BY unidad_id, tipo_bien, identificacion"
).bindparams(bindparam("unidades", expanding=True))


def listar_inventario(
    session: Session, unidades: list[int], tipo_bien: str | None
) -> list[RowMapping]:
    return list(
        session.exec(
            INVENTARIO, params={"unidades": unidades, "tipo_bien": tipo_bien}
        ).mappings()
    )
