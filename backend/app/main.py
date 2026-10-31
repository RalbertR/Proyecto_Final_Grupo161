from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from app.acceso.router import router as acceso_router
from app.consultas.router import router as consultas_router
from app.core.errores import error_de_trigger
from app.movimientos.router import router as movimientos_router
from app.organizacion.router import router as organizacion_router
from app.revision.router import router as revision_router
from app.salud.router import router as salud_router


def create_app() -> FastAPI:
    app = FastAPI(title="Sistema Logístico Policial", version="0.1.0")
    app.add_exception_handler(OperationalError, error_de_trigger)
    app.include_router(salud_router, prefix="/api")
    app.include_router(acceso_router, prefix="/api")
    app.include_router(consultas_router, prefix="/api")
    app.include_router(organizacion_router, prefix="/api")
    app.include_router(movimientos_router, prefix="/api")
    app.include_router(revision_router, prefix="/api")
    return app


app = create_app()
