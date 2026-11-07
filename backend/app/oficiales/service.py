from sqlmodel import Session

from app.acceso.schema import UsuarioPublic

from . import repository
from .schema import OficialPublic


def listar_oficiales(session: Session, usuario: UsuarioPublic) -> list[OficialPublic]:
    return [
        OficialPublic.model_validate(oficial)
        for oficial in repository.listar_activos(session, usuario.unidad.id)
    ]


def oficial_publico(session: Session, oficial_id: int | None) -> OficialPublic | None:
    oficial = repository.buscar(session, oficial_id) if oficial_id else None
    return OficialPublic.model_validate(oficial) if oficial else None
