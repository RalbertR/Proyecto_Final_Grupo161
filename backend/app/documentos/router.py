from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import FileResponse

from app.acceso.dependencias import UsuarioActualDep
from app.core.database import SessionDep

from . import service
from .schema import DocumentoPublic, DocumentosActaPublic

router = APIRouter(
    prefix="/movimientos/{movimiento_id}/documentos", tags=["Documentos"]
)


@router.get("", response_model=DocumentosActaPublic)
def listar_documentos(
    session: SessionDep, usuario: UsuarioActualDep, movimiento_id: int
):
    return service.listar_documentos(session, usuario, movimiento_id)


@router.post("", response_model=DocumentoPublic, status_code=status.HTTP_201_CREATED)
def adjuntar_documento(
    session: SessionDep,
    usuario: UsuarioActualDep,
    movimiento_id: int,
    archivo: Annotated[UploadFile, File()],
):
    return service.adjuntar_documento(session, usuario, movimiento_id, archivo)


@router.get("/{documento_id}", response_class=FileResponse)
def descargar_documento(
    session: SessionDep,
    usuario: UsuarioActualDep,
    movimiento_id: int,
    documento_id: int,
):
    return service.descargar_documento(session, usuario, movimiento_id, documento_id)
