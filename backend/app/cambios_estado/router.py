from typing import Annotated

from fastapi import APIRouter, Body, File, Form, UploadFile, status
from fastapi.responses import FileResponse

from app.acceso.dependencias import UsuarioActualDep
from app.bienes.model import EstadoOperativo
from app.core.database import SessionDep
from app.revision.schema import RevisionPublic

from . import service
from .schema import (
    CambioEstadoPublic,
    RevisionCambioObservada,
    RevisionCambioRevisado,
)

router = APIRouter(tags=["Cambios de estado"])


@router.post(
    "/bienes/{bien_id}/cambios-estado",
    response_model=CambioEstadoPublic,
    status_code=status.HTTP_201_CREATED,
)
def registrar_cambio(
    session: SessionDep,
    usuario: UsuarioActualDep,
    bien_id: int,
    estado_nuevo: Annotated[EstadoOperativo, Form()],
    observaciones: Annotated[str, Form()],
    informe: Annotated[UploadFile | None, File()] = None,
):
    return service.registrar_cambio(
        session, usuario, bien_id, estado_nuevo, observaciones, informe
    )


@router.get("/cambios-estado/{cambio_id}", response_model=CambioEstadoPublic)
def consultar_cambio(session: SessionDep, usuario: UsuarioActualDep, cambio_id: int):
    return service.consultar_cambio(session, usuario, cambio_id)


@router.get("/cambios-estado/{cambio_id}/informe", response_class=FileResponse)
def descargar_informe(session: SessionDep, usuario: UsuarioActualDep, cambio_id: int):
    return service.descargar_informe(session, usuario, cambio_id)


@router.post(
    "/cambios-estado/{cambio_id}/revisiones",
    response_model=RevisionPublic,
    status_code=status.HTTP_201_CREATED,
)
def revisar_cambio(
    session: SessionDep,
    usuario: UsuarioActualDep,
    cambio_id: int,
    revision: Annotated[
        RevisionCambioRevisado | RevisionCambioObservada,
        Body(discriminator="resultado"),
    ],
):
    return service.revisar_cambio(session, usuario, cambio_id, revision)
