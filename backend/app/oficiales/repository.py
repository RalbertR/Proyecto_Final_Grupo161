from sqlalchemy import RowMapping
from sqlmodel import Session, text

ACTIVOS = text(
    "SELECT id, legajo, CONCAT(apellido, ', ', nombre) AS nombre FROM oficial "
    "WHERE unidad_id = :unidad_id AND activo ORDER BY apellido, nombre, id"
)

BUSCAR = text(
    "SELECT id, legajo, CONCAT(apellido, ', ', nombre) AS nombre, unidad_id, activo "
    "FROM oficial WHERE id = :id"
)

BLOQUEAR = text(
    "SELECT id, legajo, CONCAT(apellido, ', ', nombre) AS nombre, unidad_id, activo "
    "FROM oficial WHERE id = :id FOR UPDATE"
)

TIPOS_ASIGNADOS = text("SELECT DISTINCT tipo_bien FROM bien WHERE oficial_id = :id")

TIENE_TRASLADO_PENDIENTE = text(
    "SELECT EXISTS (SELECT 1 FROM traslado_oficial "
    "WHERE oficial_id = :id AND estado = 'PENDIENTE')"
)


def listar_activos(session: Session, unidad_id: int) -> list[RowMapping]:
    return list(session.exec(ACTIVOS, params={"unidad_id": unidad_id}).mappings())


def buscar(session: Session, oficial_id: int) -> RowMapping | None:
    return session.exec(BUSCAR, params={"id": oficial_id}).mappings().first()


def bloquear(session: Session, oficial_id: int) -> RowMapping | None:
    return session.exec(BLOQUEAR, params={"id": oficial_id}).mappings().first()


def tipos_asignados(session: Session, oficial_id: int) -> set[str]:
    return set(session.exec(TIPOS_ASIGNADOS, params={"id": oficial_id}).scalars())


def tiene_traslado_pendiente(session: Session, oficial_id: int) -> bool:
    return bool(
        session.exec(TIENE_TRASLADO_PENDIENTE, params={"id": oficial_id}).scalar_one()
    )
