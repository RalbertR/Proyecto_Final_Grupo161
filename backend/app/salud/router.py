from fastapi import APIRouter

from app.core.database import SessionDep

from . import service
from .schema import SaludPublic

router = APIRouter(prefix="/salud", tags=["Salud"])


@router.get(
    "",
    response_model=SaludPublic,
    summary="Verificar que la API y la base respondan",
    responses={
        500: {
            "description": "La API no pudo hablar con la base de datos.",
            "content": {"text/plain": {"example": "Internal Server Error"}},
        }
    },
)
def consultar_salud(session: SessionDep):
    """No hace falta iniciar sesión. Consulta la base de datos y, si responde, devuelve
    `ok`. Sirve para comprobar que un despliegue quedó funcionando."""
    return service.consultar(session)
