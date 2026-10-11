from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

ERROR_DE_TRIGGER = 1644


async def error_de_trigger(request: Request, exc: OperationalError):
    codigo, mensaje = exc.orig.args[0], exc.orig.args[-1]
    if codigo != ERROR_DE_TRIGGER:
        raise exc
    return JSONResponse(status_code=409, content={"detail": mensaje})
