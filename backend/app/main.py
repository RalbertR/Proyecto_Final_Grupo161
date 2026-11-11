from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from app.acceso.router import router as acceso_router
from app.cambios_estado.router import router as cambios_estado_router
from app.consultas.router import router as consultas_router
from app.core.errores import error_de_trigger
from app.documentos.router import router as documentos_router
from app.movimientos.router import router as movimientos_router
from app.oficiales.router import router as oficiales_router
from app.organizacion.router import router as organizacion_router
from app.revision.router import router as revision_router
from app.salud.router import router as salud_router

DESCRIPCION = """
API del sistema que lleva la trazabilidad de los bienes logísticos de una fuerza de
seguridad: armamento, chalecos balísticos, móviles y equipos de comunicaciones. La
organización y los datos son ficticios.

## Cómo probarla desde esta página

1. Tocá el botón **Authorize** y entrá con un usuario de demostración, por ejemplo
   `aux.unidad_a`, y la contraseña `CONTRASENA_DEMO` del `.env`.
2. Listo: el token queda cargado y el resto de los endpoints lo envían solos. Fuera de
   esta página, el token se manda en el encabezado `Authorization: Bearer <token>`.

## Qué ve cada usuario

Depende de la unidad del usuario. Una Operacional ve solo lo suyo, una Regional lo
suyo y lo de sus Operacionales, y la Dirección lo de todas las unidades.

## Errores

Los errores responden `{"detail": "<mensaje en español>"}`, listo para mostrarlo en pantalla:

| Código | Cuándo |
|---|---|
| 401 | Falta el token, no es válido o venció. |
| 403 | El usuario no puede acceder a lo que pide. |
| 404 | Lo que pide no existe. |
| 409 | Lo que pide no se puede hacer en el estado actual: el bien ya tiene un movimiento pendiente, el acta ya se resolvió, la versión quedó vieja. |
| 422 | Un dato está mal o no cumple una regla. Si es un problema de formato, `detail` es una lista que indica qué campo falló. |
"""

ETIQUETAS = [
    {"name": "Acceso", "description": "Inicio de sesión y datos del usuario."},
    {
        "name": "Consultas",
        "description": "Inventario, historial de un bien y sala de situación.",
    },
    {
        "name": "Organización",
        "description": "Unidades que el usuario puede consultar y sus ubicaciones.",
    },
    {
        "name": "Movimientos",
        "description": "Entregas entre unidades, dotaciones y devoluciones de "
        "oficiales, recepción, corrección de actas devueltas y rectificaciones.",
    },
    {
        "name": "Documentos",
        "description": "Actas escaneadas en PDF adjuntas a un movimiento.",
    },
    {"name": "Oficiales", "description": "Oficiales activos de la unidad."},
    {
        "name": "Revisión",
        "description": "Bandeja y revisión de los movimientos de las unidades "
        "dependientes.",
    },
    {
        "name": "Cambios de estado",
        "description": "Pasar un bien a fuera de servicio o volverlo a servicio, "
        "con su revisión y corrección.",
    },
    {"name": "Salud", "description": "Verifica que la API y la base respondan."},
]


def create_app() -> FastAPI:
    app = FastAPI(
        title="Sistema Logístico Policial",
        version="0.1.0",
        description=DESCRIPCION,
        openapi_tags=ETIQUETAS,
        # Bajo /api para que nginx y el servidor de Vite lo dejen pasar.
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    app.add_exception_handler(OperationalError, error_de_trigger)
    app.include_router(salud_router, prefix="/api")
    app.include_router(acceso_router, prefix="/api")
    app.include_router(consultas_router, prefix="/api")
    app.include_router(organizacion_router, prefix="/api")
    app.include_router(movimientos_router, prefix="/api")
    app.include_router(documentos_router, prefix="/api")
    app.include_router(oficiales_router, prefix="/api")
    app.include_router(revision_router, prefix="/api")
    app.include_router(cambios_estado_router, prefix="/api")
    return app


app = create_app()
