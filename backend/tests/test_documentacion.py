"""Guarda de la documentación de la API: cada endpoint se explica en Swagger.

Si se agrega un endpoint sin descripción, ejemplo o errores, estas pruebas fallan.
"""

import pytest

METODOS = {"get", "post", "put", "patch", "delete"}
SIN_SESION = {"/api/salud", "/api/auth/login"}


@pytest.fixture
def openapi(client):
    return client.get("/api/openapi.json").json()


def operaciones(openapi):
    for ruta, metodos in openapi["paths"].items():
        for metodo, operacion in metodos.items():
            if metodo in METODOS:
                yield ruta, metodo, operacion


def resuelto(openapi, esquema):
    """Sigue un `$ref` de `components/schemas`."""
    while "$ref" in esquema:
        esquema = openapi["components"]["schemas"][esquema["$ref"].split("/")[-1]]
    return esquema


def tiene_ejemplo(openapi, esquema):
    esquema = resuelto(openapi, esquema)
    if "examples" in esquema or "example" in esquema:
        return True
    if esquema.get("type") == "array":
        return tiene_ejemplo(openapi, esquema["items"])
    return any(
        tiene_ejemplo(openapi, variante)
        for variante in esquema.get("anyOf", []) + esquema.get("oneOf", [])
    )


def contenido_con_ejemplo(openapi, contenido):
    for medio in contenido.values():
        if "examples" in medio or "example" in medio:
            return True
        if "schema" in medio and tiene_ejemplo(openapi, medio["schema"]):
            return True
    return False


def test_swagger_se_publica_bajo_api(client):
    assert client.get("/api/docs").status_code == 200
    assert client.get("/api/redoc").status_code == 200
    assert client.get("/api/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 404


def test_cada_endpoint_tiene_resumen_y_descripcion(openapi):
    sin_explicar = [
        f"{metodo.upper()} {ruta}"
        for ruta, metodo, operacion in operaciones(openapi)
        if not operacion.get("summary") or not operacion.get("description")
    ]
    assert sin_explicar == []


def test_cada_endpoint_tiene_un_ejemplo(openapi):
    """Un ejemplo en lo que recibe, en lo que devuelve o en un error."""
    sin_ejemplo = []
    for ruta, metodo, operacion in operaciones(openapi):
        cuerpo = operacion.get("requestBody", {}).get("content", {})
        respuestas = operacion["responses"].values()
        hay_ejemplo = contenido_con_ejemplo(openapi, cuerpo) or any(
            contenido_con_ejemplo(openapi, respuesta.get("content", {}))
            for respuesta in respuestas
        )
        if not hay_ejemplo:
            sin_ejemplo.append(f"{metodo.upper()} {ruta}")
    assert sin_ejemplo == []


def test_cada_endpoint_documenta_sus_errores(openapi):
    sin_errores = []
    for ruta, metodo, operacion in operaciones(openapi):
        codigos = {int(codigo) for codigo in operacion["responses"] if codigo.isdigit()}
        errores = {codigo for codigo in codigos if codigo >= 400}
        if not errores:
            sin_errores.append(f"{metodo.upper()} {ruta}")
        elif ruta not in SIN_SESION and 401 not in errores:
            sin_errores.append(f"{metodo.upper()} {ruta} (falta el 401)")
    assert sin_errores == []


def test_los_errores_traen_un_ejemplo_con_el_mensaje(openapi):
    sin_ejemplo = []
    for ruta, metodo, operacion in operaciones(openapi):
        for codigo, respuesta in operacion["responses"].items():
            if codigo in {"401", "403", "404", "409", "422"} and not (
                contenido_con_ejemplo(openapi, respuesta.get("content", {}))
            ):
                sin_ejemplo.append(f"{metodo.upper()} {ruta} {codigo}")
    assert sin_ejemplo == []
