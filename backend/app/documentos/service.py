import hashlib
import os
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pypdf import PdfReader
from pypdf.errors import FileNotDecryptedError, PyPdfError
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.acceso.schema import UsuarioPublic
from app.core.config import DIRECTORIO_DOCUMENTOS
from app.movimientos.service import consultar_movimiento

from . import repository
from .schema import DocumentoPublic, DocumentosActaPublic

MAXIMO_BYTES = 10 * 1024 * 1024


def unidad_del_acta(session: Session, movimiento_id: int) -> int:
    unidad_id = repository.unidad_registrante(session, movimiento_id)
    if unidad_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="El movimiento no existe"
        )
    return unidad_id


def listar_documentos(
    session: Session, usuario: UsuarioPublic, movimiento_id: int
) -> DocumentosActaPublic:
    consultar_movimiento(session, usuario, movimiento_id)
    return DocumentosActaPublic(
        documentos=[
            DocumentoPublic.model_validate(documento)
            for documento in repository.listar_documentos(session, movimiento_id)
        ],
        puede_adjuntar=unidad_del_acta(session, movimiento_id) == usuario.unidad.id,
    )


def pdf_invalido() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="El archivo tiene que ser un PDF válido",
    )


def validar_archivo(archivo: UploadFile) -> tuple[str, bytes]:
    # El nombre solo se conserva como metadato y para la descarga.
    nombre = (archivo.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    nombre = "".join(caracter for caracter in nombre if caracter.isprintable()).strip()
    if not nombre or len(nombre) > 255 or not nombre.lower().endswith(".pdf"):
        raise pdf_invalido()
    mime = (archivo.content_type or "").split(";", 1)[0].strip().lower()
    if mime != "application/pdf":
        raise pdf_invalido()
    contenido = archivo.file.read(MAXIMO_BYTES + 1)
    if len(contenido) > MAXIMO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El PDF no puede superar los 10 MB",
        )
    if not contenido.startswith(b"%PDF-"):
        raise pdf_invalido()
    try:
        lector = PdfReader(BytesIO(contenido), strict=False)
        if lector.is_encrypted and not lector.decrypt(""):
            raise FileNotDecryptedError()
        if lector.root_object.get("/Type") != "/Catalog" or not len(lector.pages):
            raise pdf_invalido()
    except FileNotDecryptedError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El PDF requiere una contraseña y no se puede validar",
        ) from error
    except (
        PyPdfError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        RecursionError,
    ) as error:
        raise pdf_invalido() from error
    return nombre, contenido


def duplicado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail="El PDF ya está cargado"
    )


def guardar_pdf(
    session: Session, usuario_id: int, archivo: UploadFile
) -> tuple[int, Path]:
    nombre, contenido = validar_archivo(archivo)
    hash_sha256 = hashlib.sha256(contenido).hexdigest()
    if repository.hash_cargado(session, hash_sha256):
        raise duplicado()

    directorio = Path(DIRECTORIO_DOCUMENTOS)
    nombre_generado = f"{uuid4().hex}.pdf"
    ruta = directorio / nombre_generado
    directorio.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(ruta, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as destino:
            destino.write(contenido)
        documento_id = repository.insertar_documento(
            session,
            nombre_original=nombre,
            tamano_bytes=len(contenido),
            hash_sha256=hash_sha256,
            ruta_almacenamiento=nombre_generado,
            usuario_id=usuario_id,
        )
    except Exception:
        ruta.unlink(missing_ok=True)
        raise
    return documento_id, ruta


def deshacer_guardado(session: Session, ruta: Path | None, error: Exception) -> None:
    session.rollback()
    if ruta is not None:
        ruta.unlink(missing_ok=True)
    if isinstance(error, IntegrityError) and "uq_documento_hash" in str(error.orig):
        raise duplicado() from error
    if isinstance(error, OSError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo guardar el documento. Intente de nuevo",
        ) from error


def entregar_pdf(ruta_almacenamiento: str, nombre_original: str) -> FileResponse:
    directorio = Path(DIRECTORIO_DOCUMENTOS).resolve()
    ruta = (directorio / ruta_almacenamiento).resolve()
    if not ruta.is_relative_to(directorio) or not ruta.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El archivo del documento no está disponible",
        )
    return FileResponse(
        ruta,
        media_type="application/pdf",
        filename=nombre_original,
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


def adjuntar_documento(
    session: Session, usuario: UsuarioPublic, movimiento_id: int, archivo: UploadFile
) -> DocumentoPublic:
    if unidad_del_acta(session, movimiento_id) != usuario.unidad.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo la unidad que registró el movimiento puede adjuntar documentos",
        )
    ruta = None
    try:
        documento_id, ruta = guardar_pdf(session, usuario.id, archivo)
        repository.vincular_documento(session, movimiento_id, documento_id)
        documento = DocumentoPublic.model_validate(
            repository.buscar_documento(session, movimiento_id, documento_id)
        )
        session.commit()
    except Exception as error:
        deshacer_guardado(session, ruta, error)
        raise
    return documento


def descargar_documento(
    session: Session, usuario: UsuarioPublic, movimiento_id: int, documento_id: int
) -> FileResponse:
    consultar_movimiento(session, usuario, movimiento_id)
    documento = repository.buscar_documento(session, movimiento_id, documento_id)
    if documento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El documento no está asociado a ese movimiento",
        )
    return entregar_pdf(documento["ruta_almacenamiento"], documento["nombre_original"])
