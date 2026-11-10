from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import FileResponse

from app.acceso.dependencias import UsuarioActualDep
from app.core.database import SessionDep
from app.core.documentacion import SIN_SESION, error, error_422, pdf

from . import service
from .schema import DocumentoPublic, DocumentosActaPublic

router = APIRouter(
    prefix="/movimientos/{movimiento_id}/documentos",
    tags=["Documentos"],
    responses=SIN_SESION,
)

NO_EXISTE = error("El movimiento no existe.", "El movimiento no existe")
SIN_ACCESO = (
    "El acta no es de su unidad ni de una unidad que dependa de la suya, y su unidad "
    "tampoco tiene hoy ninguno de los bienes."
)


@router.get(
    "",
    response_model=DocumentosActaPublic,
    summary="Listar los PDFs de un acta",
    responses={
        403: error(SIN_ACCESO, "No tiene acceso a ese movimiento"),
        404: NO_EXISTE,
        422: error_422("El identificador del movimiento no es un número."),
    },
)
def listar_documentos(
    session: SessionDep, usuario: UsuarioActualDep, movimiento_id: int
):
    """Devuelve los datos de los PDFs adjuntos al acta, y si su unidad puede adjuntar
    otro. Solo puede adjuntar la unidad que registró el movimiento."""
    return service.listar_documentos(session, usuario, movimiento_id)


@router.post(
    "",
    response_model=DocumentoPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Adjuntar el acta escaneada",
    responses={
        403: error(
            "Solo adjunta la unidad que registró el movimiento.",
            "Solo la unidad que registró el movimiento puede adjuntar documentos",
        ),
        404: NO_EXISTE,
        409: error(
            "Ese mismo PDF ya está cargado, aunque tenga otro nombre o sea de otra "
            "acta.",
            "El PDF ya está cargado",
        ),
        422: error_422(
            "El archivo no es un PDF válido, tiene contraseña o pesa más de 10 MiB.",
            "El archivo tiene que ser un PDF válido",
            "El PDF no puede superar los 10 MB",
            "El PDF requiere una contraseña y no se puede validar",
        ),
    },
)
def adjuntar_documento(
    session: SessionDep,
    usuario: UsuarioActualDep,
    movimiento_id: int,
    archivo: Annotated[UploadFile, File(description="El acta firmada, en PDF.")],
):
    """Adjunta el acta escaneada. Se envía como formulario (`multipart/form-data`),
    en el campo `archivo`.

    Se guardan el nombre, el tamaño, el usuario y la fecha, y el archivo queda en una
    carpeta privada con un nombre generado. Una vez adjuntado no se puede reemplazar
    ni borrar. Hay más detalle en `docs/contratos/documentos.md`."""
    return service.adjuntar_documento(session, usuario, movimiento_id, archivo)


@router.get(
    "/{documento_id}",
    response_class=FileResponse,
    summary="Descargar un PDF del acta",
    responses={
        200: pdf("El PDF original, con su nombre original."),
        403: error(SIN_ACCESO, "No tiene acceso a ese movimiento"),
        404: error(
            "El movimiento no existe, el documento no es de ese movimiento o el "
            "archivo no está disponible en el servidor.",
            "El movimiento no existe",
            "El documento no está asociado a ese movimiento",
            "El archivo del documento no está disponible",
        ),
        422: error_422("Alguno de los identificadores no es un número."),
    },
)
def descargar_documento(
    session: SessionDep,
    usuario: UsuarioActualDep,
    movimiento_id: int,
    documento_id: int,
):
    """Descarga el PDF. Hay que estar autenticado: el archivo no se puede abrir desde
    una dirección pública."""
    return service.descargar_documento(session, usuario, movimiento_id, documento_id)
