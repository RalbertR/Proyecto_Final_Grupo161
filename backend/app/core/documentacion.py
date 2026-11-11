"""Metadatos de Swagger: formato de los errores y ejemplos de la documentación.

Los routers siguen finos: acá solo hay datos para `/api/docs`, sin lógica.
"""

from typing import Any

from pydantic import BaseModel


class ErrorPublic(BaseModel):
    """Error de negocio: un texto en español listo para mostrar en pantalla."""

    detail: str


class DetalleValidacion(BaseModel):
    type: str
    loc: list[str | int]
    msg: str
    input: Any = None


class ErrorValidacion(BaseModel):
    """Error de formato de los datos enviados, con el campo que falló."""

    detail: list[DetalleValidacion]


EJEMPLO_VALIDACION = {
    "detail": [
        {
            "type": "string_pattern_mismatch",
            "loc": ["body", "numero_acta"],
            "msg": "String should match pattern '^[0-9]{4}/[0-9]{4}$'",
            "input": "12/26",
        }
    ]
}


def _ejemplos(mensajes: tuple[str, ...]) -> dict[str, Any]:
    return {
        f"ejemplo_{numero}": {"summary": mensaje, "value": {"detail": mensaje}}
        for numero, mensaje in enumerate(mensajes, start=1)
    }


def error(descripcion: str, *mensajes: str) -> dict[str, Any]:
    """Entrada de `responses` para un error con los mensajes que puede devolver."""
    return {
        "model": ErrorPublic,
        "description": descripcion,
        "content": {"application/json": {"examples": _ejemplos(mensajes)}},
    }


def error_422(descripcion: str, *mensajes: str) -> dict[str, Any]:
    """Como `error`, más el formato de validación de Pydantic.

    Al declarar un 422, FastAPI deja de agregar el suyo, así que se repite acá.
    """
    ejemplos = _ejemplos(mensajes)
    ejemplos["validacion"] = {
        "summary": "Un dato no cumple el formato",
        "value": EJEMPLO_VALIDACION,
    }
    return {
        "model": ErrorPublic | ErrorValidacion,
        "description": descripcion,
        "content": {"application/json": {"examples": ejemplos}},
    }


def pdf(descripcion: str) -> dict[str, Any]:
    """Entrada de `responses` para una descarga de PDF."""
    return {
        "description": descripcion,
        "content": {
            "application/pdf": {"schema": {"type": "string", "format": "binary"}}
        },
    }


SIN_SESION: dict[int | str, dict[str, Any]] = {
    401: error(
        "Falta el token de sesión, o es inválido o venció.",
        "Sesión no válida o vencida",
    )
}

# Ejemplos compartidos, tomados de los datos de demostración.
UNIDAD_A = {"id": 4, "nombre": "Unidad Operacional A", "nivel": "OPERACIONAL"}
UNIDAD_B = {"id": 5, "nombre": "Unidad Operacional B", "nivel": "OPERACIONAL"}
REGIONAL_NORTE = {"id": 2, "nombre": "Unidad Regional Norte", "nivel": "REGIONAL"}
OFICIAL = {"id": 12, "legajo": "10003", "nombre": "Acosta, Lucas"}
