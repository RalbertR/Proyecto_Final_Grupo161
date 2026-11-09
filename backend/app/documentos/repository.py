from sqlalchemy import RowMapping
from sqlmodel import Session, text

UNIDAD_REGISTRANTE = text("SELECT unidad_registrante_id FROM movimiento WHERE id = :id")

HASH_CARGADO = text("SELECT id FROM documento WHERE hash_sha256 = :hash_sha256")

INSERTAR_DOCUMENTO = text(
    "INSERT INTO documento (nombre_original, tipo_mime, tamano_bytes, hash_sha256, "
    "ruta_almacenamiento, usuario_id) VALUES (:nombre_original, 'application/pdf', "
    ":tamano_bytes, :hash_sha256, :ruta_almacenamiento, :usuario_id)"
)

VINCULAR_DOCUMENTO = text(
    "INSERT INTO movimiento_documento (movimiento_id, documento_id) "
    "VALUES (:movimiento_id, :documento_id)"
)

DATOS_DOCUMENTOS = (
    "SELECT d.id, d.nombre_original, d.tipo_mime, d.tamano_bytes, d.hash_sha256, "
    "d.ruta_almacenamiento, u.nombre_usuario AS usuario, d.fecha_carga "
    "FROM documento d JOIN movimiento_documento md ON md.documento_id = d.id "
    "JOIN usuario u ON u.id = d.usuario_id WHERE md.movimiento_id = :movimiento_id"
)

DOCUMENTOS_DEL_MOVIMIENTO = text(DATOS_DOCUMENTOS + " ORDER BY d.id")
DOCUMENTO_DEL_MOVIMIENTO = text(DATOS_DOCUMENTOS + " AND d.id = :documento_id")


def unidad_registrante(session: Session, movimiento_id: int) -> int | None:
    return session.exec(UNIDAD_REGISTRANTE, params={"id": movimiento_id}).scalar()


def hash_cargado(session: Session, hash_sha256: str) -> bool:
    return (
        session.exec(HASH_CARGADO, params={"hash_sha256": hash_sha256}).first()
        is not None
    )


def insertar_documento(session: Session, **valores) -> int:
    return session.exec(INSERTAR_DOCUMENTO, params=valores).lastrowid


def vincular_documento(session: Session, movimiento_id: int, documento_id: int) -> None:
    session.exec(
        VINCULAR_DOCUMENTO,
        params={"movimiento_id": movimiento_id, "documento_id": documento_id},
    )


def listar_documentos(session: Session, movimiento_id: int) -> list[RowMapping]:
    return list(
        session.exec(
            DOCUMENTOS_DEL_MOVIMIENTO, params={"movimiento_id": movimiento_id}
        ).mappings()
    )


def buscar_documento(
    session: Session, movimiento_id: int, documento_id: int
) -> RowMapping | None:
    return (
        session.exec(
            DOCUMENTO_DEL_MOVIMIENTO,
            params={"movimiento_id": movimiento_id, "documento_id": documento_id},
        )
        .mappings()
        .first()
    )
