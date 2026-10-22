from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from app.acceso.router import router as acceso_router
from app.core.errores import error_de_trigger
from app.salud.router import router as salud_router


def create_app() -> FastAPI:
    app = FastAPI(title="Sistema Logístico Policial", version="0.1.0")
    app.add_exception_handler(OperationalError, error_de_trigger)
    app.include_router(salud_router, prefix="/api")
    app.include_router(acceso_router, prefix="/api")
    return app


app = create_app()
