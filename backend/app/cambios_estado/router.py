from typing import Annotated

from fastapi import APIRouter, Body, File, Form, UploadFile, status
from fastapi.responses import FileResponse

from app.acceso.dependencias import UsuarioActualDep
from app.bienes.model import EstadoOperativo
from app.core.database import SessionDep
from app.core.documentacion import SIN_SESION, error, error_422, pdf
from app.revision.schema import RevisionPublic

from . import service
from .schema import (
    CambioEstadoPublic,
    RevisionCambioObservada,
    RevisionCambioRevisado,
)

router = APIRouter(tags=["Cambios de estado"], responses=SIN_SESION)

NO_EXISTE = error("El cambio de estado no existe.", "El cambio de estado no existe")
SIN_ACCESO = error(
    "No puede ver el historial de ese bien y tampoco es de la unidad que registró el "
    "cambio ni de la que la supervisa.",
    "No tiene acceso a ese cambio de estado",
)
VERSION_VENCIDA = "La revisión no corresponde a la versión vigente"


@router.post(
    "/bienes/{bien_id}/cambios-estado",
    response_model=CambioEstadoPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Cambiar el estado de servicio de un bien",
    responses={
        403: error(
            "El bien no es de su unidad.",
            "Solo la unidad dueña del bien puede cambiar su estado",
        ),
        404: error("El bien no existe.", "El bien no existe"),
        409: error(
            "El bien está dado de baja, ya está en ese estado o tiene un movimiento "
            "pendiente o devuelto.",
            "El bien está dado de baja",
            "El bien ya está en ese estado",
            "El bien tiene un movimiento pendiente",
        ),
        422: error_422(
            "Falta el informe técnico al pasar a fuera de servicio, faltan las "
            "observaciones o pasan de 500 caracteres, o el archivo no es un PDF "
            "válido.",
            "El informe técnico en PDF es obligatorio para pasar a fuera de servicio",
            "Falta completar observaciones",
            "El archivo tiene que ser un PDF válido",
        ),
    },
)
def registrar_cambio(
    session: SessionDep,
    usuario: UsuarioActualDep,
    bien_id: int,
    estado_nuevo: Annotated[
        EstadoOperativo,
        Form(description="Estado al que pasa el bien.", examples=["FUERA_DE_SERVICIO"]),
    ],
    observaciones: Annotated[
        str,
        Form(
            description="De 1 a 500 caracteres. Por qué quedó fuera de servicio, o "
            "qué se reparó.",
            examples=["No transmite. Se golpeó en un procedimiento."],
        ),
    ],
    informe: Annotated[
        UploadFile | None,
        File(
            description="PDF. Es obligatorio para pasar a fuera de servicio y "
            "opcional para volver a servicio."
        ),
    ] = None,
):
    """Registra que un bien quedó fuera de servicio o que volvió a servicio. Se envía
    como formulario (`multipart/form-data`).

    No es un movimiento: no lleva acta y el bien conserva su unidad, su ubicación y
    su oficial. Un bien en dotación sigue asignado al oficial.

    Lo que registra una Operacional o una Regional queda pendiente de revisión de su
    superior. Lo que registra la Dirección no se revisa. Si algo falla, no queda ni
    el PDF ni el cambio. Hay más detalle en `docs/contratos/cambios_estado.md`.
    """
    return service.registrar_cambio(
        session, usuario, bien_id, estado_nuevo, observaciones, informe
    )


@router.get(
    "/cambios-estado/observados",
    response_model=list[CambioEstadoPublic],
    summary="Listar los cambios de estado observados",
)
def listar_observados(session: SessionDep, usuario: UsuarioActualDep):
    """Devuelve los cambios de estado que registró su unidad y que su superior
    observó. El motivo está en `revisiones`."""
    return service.listar_observados(session, usuario)


@router.post(
    "/cambios-estado/{cambio_id}/rectificaciones",
    response_model=CambioEstadoPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Corregir un cambio de estado observado",
    responses={
        403: error(
            "Solo corrige el cambio la unidad que lo registró.",
            "Solo la unidad que registró el cambio puede corregirlo",
        ),
        404: NO_EXISTE,
        409: error(
            "El cambio no está observado, o `version` ya no es la vigente.",
            "El cambio de estado no está observado",
            VERSION_VENCIDA,
        ),
        422: error_422(
            "Falta el motivo o las observaciones, o se intentó quitar el informe de "
            "un pase a fuera de servicio.",
            "Falta completar motivo",
            "Solo se puede quitar el informe de una vuelta a servicio",
        ),
    },
)
def rectificar_cambio(
    session: SessionDep,
    usuario: UsuarioActualDep,
    cambio_id: int,
    version: Annotated[
        int,
        Form(
            ge=0,
            le=65535,
            description="La versión vigente del cambio, que es la que se corrige.",
            examples=[0],
        ),
    ],
    observaciones: Annotated[
        str,
        Form(
            description="De 1 a 500 caracteres.",
            examples=["Se adjuntó el informe firmado."],
        ),
    ],
    motivo: Annotated[
        str,
        Form(
            description="Por qué se hace la corrección.",
            examples=["El informe técnico no estaba firmado"],
        ),
    ],
    informe: Annotated[
        UploadFile | None,
        File(description="PDF que reemplaza al informe actual."),
    ] = None,
    quitar_informe: Annotated[
        bool,
        Form(description="Solo en una vuelta a servicio: deja el cambio sin informe."),
    ] = False,
):
    """Guarda una corrección del cambio como versión nueva y lo deja otra vez
    pendiente de revisión. El estado del bien no cambia.

    En un pase a fuera de servicio se puede reemplazar el informe, pero no quitarlo.
    """
    return service.rectificar_cambio(
        session,
        usuario,
        cambio_id,
        version,
        observaciones,
        motivo,
        informe,
        quitar_informe,
    )


@router.get(
    "/cambios-estado/{cambio_id}",
    response_model=CambioEstadoPublic,
    summary="Consultar un cambio de estado",
    responses={
        403: SIN_ACCESO,
        404: NO_EXISTE,
        422: error_422("El identificador del cambio no es un número."),
    },
)
def consultar_cambio(session: SessionDep, usuario: UsuarioActualDep, cambio_id: int):
    """Devuelve el cambio con las observaciones y el informe vigentes, sus revisiones
    y sus correcciones."""
    return service.consultar_cambio(session, usuario, cambio_id)


@router.get(
    "/cambios-estado/{cambio_id}/informe",
    response_class=FileResponse,
    summary="Descargar el informe de un cambio de estado",
    responses={
        200: pdf("El PDF vigente, con su nombre original."),
        403: SIN_ACCESO,
        404: error(
            "El cambio no existe, no tiene informe o el archivo no está disponible.",
            "El cambio de estado no existe",
            "El cambio de estado no tiene informe",
            "El archivo del documento no está disponible",
        ),
        422: error_422("El identificador del cambio no es un número."),
    },
)
def descargar_informe(session: SessionDep, usuario: UsuarioActualDep, cambio_id: int):
    """Descarga el informe técnico, o el de puesta en servicio. Hay que estar
    autenticado."""
    return service.descargar_informe(session, usuario, cambio_id)


@router.post(
    "/cambios-estado/{cambio_id}/revisiones",
    response_model=RevisionPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Revisar un cambio de estado",
    responses={
        403: error(
            "Solo revisa la unidad que está inmediatamente por encima de la que "
            "registró el cambio.",
            "Solo el superior inmediato de la unidad revisa el cambio de estado",
        ),
        404: NO_EXISTE,
        409: error(
            "El cambio ya fue revisado u observado, o `version` ya no es la vigente.",
            "El cambio de estado no está pendiente de revisión",
            VERSION_VENCIDA,
        ),
        422: error_422("Una observación sin motivo, o una `version` fuera de rango."),
    },
)
def revisar_cambio(
    session: SessionDep,
    usuario: UsuarioActualDep,
    cambio_id: int,
    revision: Annotated[
        RevisionCambioRevisado | RevisionCambioObservada,
        Body(
            discriminator="resultado",
            openapi_examples={
                "revisado": {
                    "summary": "Confirmar el cambio",
                    "value": {"resultado": "REVISADO", "version": 0},
                },
                "observado": {
                    "summary": "Observar con un motivo",
                    "value": {
                        "resultado": "OBSERVADO",
                        "version": 0,
                        "motivo_observacion": "El informe no está firmado",
                    },
                },
            },
        ),
    ],
):
    """Funciona igual que la revisión de un movimiento: `version` tiene que ser la
    vigente y solo revisa la unidad que supervisa a la que registró el cambio."""
    return service.revisar_cambio(session, usuario, cambio_id, revision)
