from fastapi import HTTPException, status
from sqlmodel import Session

from app.acceso.schema import UsuarioPublic
from app.organizacion.model import Unidad

from . import repository
from .schema import (
    RegistroBandejaPublic,
    RevisionObservada,
    RevisionPublic,
    RevisionRevisado,
)


def listar_bandeja(
    session: Session, usuario: UsuarioPublic
) -> list[RegistroBandejaPublic]:
    return [
        RegistroBandejaPublic.model_validate(fila)
        for fila in repository.listar_bandeja(session, usuario.unidad.id)
    ]


def revisar_movimiento(
    session: Session,
    usuario: UsuarioPublic,
    movimiento_id: int,
    revision: RevisionRevisado | RevisionObservada,
) -> RevisionPublic:
    # Se bloquea antes de leer el estado: otra revisión espera acá y, con
    # READ COMMITTED, al seguir ve el movimiento ya revisado (ADR 0001).
    movimiento = repository.bloquear_movimiento(session, movimiento_id)
    if movimiento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="El movimiento no existe"
        )
    registrante = session.get(Unidad, movimiento["unidad_registrante_id"])
    if registrante.unidad_superior_id != usuario.unidad.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el superior inmediato de la unidad revisa el movimiento",
        )
    if (
        movimiento["estado"] != "APLICADO"
        or movimiento["estado_revision"] != "PENDIENTE"
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El movimiento no está pendiente de revisión",
        )
    motivo_observacion = (
        revision.motivo_observacion if isinstance(revision, RevisionObservada) else None
    )
    # Si el autor lo rectificó, trg_revision_version rechaza la versión (ADR 0007).
    revision_id = repository.insertar_revision(
        session,
        movimiento_id=movimiento_id,
        resultado=revision.resultado,
        motivo_observacion=motivo_observacion,
        version_revisada=revision.version,
        usuario_id=usuario.id,
    )
    repository.cambiar_estado_revision(session, movimiento_id, revision.resultado)
    session.commit()
    return RevisionPublic.model_validate(
        repository.buscar_revision(session, revision_id)
    )
