from fastapi import FastAPI

from app.salud.router import router as salud_router


def create_app() -> FastAPI:
    app = FastAPI(title="Sistema Logístico Policial", version="0.1.0")
    app.include_router(salud_router, prefix="/api")
    return app


app = create_app()
