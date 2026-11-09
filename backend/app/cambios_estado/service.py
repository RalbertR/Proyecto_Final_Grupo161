from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import RowMapping
from sqlmodel import Session

from app.acceso.schema import UsuarioPublic
from app.acceso.service import unidades_visibles
from app.bienes.model import EstadoOperativo
from app.documentos.service import deshacer_guardado, entregar_pdf, guardar_pdf
from app.organizacion.model import Nivel, Unidad
from app.revision import repository as revision_repository
from app.revision.schema import RevisionPublic

from . import repository
from .schema import (
    CambioEstadoPublic,
    RevisionCambioObservada,
    RevisionCambioRevisado,
)

MAXIMO_TEXTO = 500


def texto_obligatorio(valor: str, campo: str) -> str:
    limpio = valor.strip()
    if not limpio:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Falta completar {campo}",
        )
    if len(limpio) > MAXIMO_TEXTO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"El texto de {campo} no puede superar los 500 caracteres",
        )
    return limpio


def no_existe() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="El cambio de estado no existe"
    )


def conflicto(detalle: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detalle)


def publico(session: Session, fila: RowMapping) -> CambioEstadoPublic:
    informe = (
        {
            "id": fila["documento_id"],
            "nombre_original": fila["nombre_original"],
            "tamano_bytes": fila["tamano_bytes"],
        }
        if fila["documento_id"] is not None
        else None
    )
    return CambioEstadoPublic.model_validate(
        dict(fila)
        | {
            "bien": {
                "id": fila["bien_id"],
                "identificacion": fila["identificacion"],
                "tipo_bien": fila["tipo_bien"],
                "marca": fila["marca"],
                "modelo": fila["modelo"],
            },
            "informe": informe,
            "revisiones": [
                dict(revision)
                for revision in repository.listar_revisiones(session, fila["id"])
            ],
            "rectificaciones": [
                dict(rectificacion)
                for rectificacion in repository.listar_rectificaciones(
                    session, fila["id"]
                )
            ],
        }
    )


def detalle_cambio(session: Session, cambio_id: int) -> CambioEstadoPublic:
    fila = repository.buscar_cambio(session, cambio_id)
    if fila is None:
        raise no_existe()
    return publico(session, fila)


def cambio_visible(
    session: Session, usuario: UsuarioPublic, cambio_id: int
) -> RowMapping:
    fila = repository.buscar_cambio(session, cambio_id)
    if fila is None:
        raise no_existe()
    propia = usuario.unidad.id
    if propia in (fila["unidad_registrante_id"], fila["unidad_superior_id"]):
        return fila
    if fila["unidad_bien_id"] in {u.id for u in unidades_visibles(session, usuario)}:
        return fila
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tiene acceso a ese cambio de estado",
    )


def consultar_cambio(
    session: Session, usuario: UsuarioPublic, cambio_id: int
) -> CambioEstadoPublic:
    return publico(session, cambio_visible(session, usuario, cambio_id))


def descargar_informe(
    session: Session, usuario: UsuarioPublic, cambio_id: int
) -> FileResponse:
    fila = cambio_visible(session, usuario, cambio_id)
    if fila["documento_id"] is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El cambio de estado no tiene informe",
        )
    return entregar_pdf(fila["ruta_almacenamiento"], fila["nombre_original"])


def registrar_cambio(
    session: Session,
    usuario: UsuarioPublic,
    bien_id: int,
    estado_nuevo: EstadoOperativo,
    observaciones: str,
    informe: UploadFile | None,
) -> CambioEstadoPublic:
    observaciones = texto_obligatorio(observaciones, "las observaciones")
    if informe is None and estado_nuevo == EstadoOperativo.FUERA_DE_SERVICIO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El informe técnico en PDF es obligatorio para pasar a fuera de servicio",
        )
    bien = repository.bloquear_bien(session, bien_id)
    if bien is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="El bien no existe"
        )
    if bien["unidad_id"] != usuario.unidad.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo la unidad dueña del bien puede cambiar su estado",
        )
    if bien["de_baja"]:
        raise conflicto("El bien está dado de baja")
    if bien["estado_operativo"] == estado_nuevo:
        raise conflicto("El bien ya está en ese estado")
    if repository.con_movimiento_pendiente(session, bien_id):
        raise conflicto("El bien tiene un movimiento pendiente")

    ruta = None
    try:
        documento_id = None
        if informe is not None:
            documento_id, ruta = guardar_pdf(session, usuario.id, informe)
        cambio_id = repository.insertar_cambio(
            session,
            bien_id=bien_id,
            estado_anterior=bien["estado_operativo"],
            estado_nuevo=estado_nuevo.value,
            observaciones=observaciones,
            documento_id=documento_id,
            estado_revision=(
                "NO_APLICA" if usuario.unidad.nivel == Nivel.DIRECCION else "PENDIENTE"
            ),
            usuario_id=usuario.id,
            unidad_registrante_id=usuario.unidad.id,
        )
        repository.cambiar_estado_bien(session, bien_id, estado_nuevo.value)
        session.commit()
    except Exception as error:
        deshacer_guardado(session, ruta, error)
        raise
    return detalle_cambio(session, cambio_id)


def version_vencida() -> HTTPException:
    return conflicto("La revisión no corresponde a la versión vigente")


def revisar_cambio(
    session: Session,
    usuario: UsuarioPublic,
    cambio_id: int,
    revision: RevisionCambioRevisado | RevisionCambioObservada,
) -> RevisionPublic:
    cambio = repository.bloquear_cambio(session, cambio_id)
    if cambio is None:
        raise no_existe()
    registrante = session.get(Unidad, cambio["unidad_registrante_id"])
    if registrante.unidad_superior_id != usuario.unidad.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el superior inmediato de la unidad revisa el cambio de estado",
        )
    if cambio["estado"] != "APLICADO" or cambio["estado_revision"] != "PENDIENTE":
        raise conflicto("El cambio de estado no está pendiente de revisión")
    if revision.version != cambio["version_vigente"]:
        raise version_vencida()
    revision_id = revision_repository.insertar_revision(
        session,
        movimiento_id=None,
        cambio_estado_id=cambio_id,
        resultado=revision.resultado,
        motivo_observacion=(
            revision.motivo_observacion
            if isinstance(revision, RevisionCambioObservada)
            else None
        ),
        version_revisada=revision.version,
        usuario_id=usuario.id,
    )
    repository.cambiar_estado_revision(session, cambio_id, revision.resultado)
    session.commit()
    return RevisionPublic.model_validate(
        revision_repository.buscar_revision(session, revision_id)
    )


def listar_observados(
    session: Session, usuario: UsuarioPublic
) -> list[CambioEstadoPublic]:
    return [
        publico(session, fila)
        for fila in repository.listar_observados(session, usuario.unidad.id)
    ]


def solo_vuelta_a_servicio() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="Solo se puede quitar el informe de una vuelta a servicio",
    )


def rectificar_cambio(
    session: Session,
    usuario: UsuarioPublic,
    cambio_id: int,
    version: int,
    observaciones: str,
    motivo: str,
    informe: UploadFile | None,
    quitar_informe: bool,
) -> CambioEstadoPublic:
    observaciones = texto_obligatorio(observaciones, "las observaciones")
    motivo = texto_obligatorio(motivo, "el motivo")
    if quitar_informe and informe is not None:
        raise solo_vuelta_a_servicio()
    cambio = repository.bloquear_cambio(session, cambio_id)
    if cambio is None:
        raise no_existe()
    if cambio["unidad_registrante_id"] != usuario.unidad.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo la unidad que registró el cambio puede corregirlo",
        )
    if cambio["estado"] != "APLICADO" or cambio["estado_revision"] != "OBSERVADO":
        raise conflicto("El cambio de estado no está observado")
    if version != cambio["version_vigente"]:
        raise version_vencida()
    if quitar_informe and cambio["estado_nuevo"] == EstadoOperativo.FUERA_DE_SERVICIO:
        raise solo_vuelta_a_servicio()

    ruta = None
    try:
        documento_id = None if quitar_informe else cambio["documento_id"]
        if informe is not None:
            documento_id, ruta = guardar_pdf(session, usuario.id, informe)
        repository.insertar_rectificacion(
            session,
            cambio_estado_id=cambio_id,
            version=cambio["version_vigente"] + 1,
            observaciones=observaciones,
            documento_id=documento_id,
            motivo=motivo,
            usuario_id=usuario.id,
        )
        repository.cambiar_estado_revision(session, cambio_id, "PENDIENTE")
        session.commit()
    except Exception as error:
        deshacer_guardado(session, ruta, error)
        raise
    return detalle_cambio(session, cambio_id)
