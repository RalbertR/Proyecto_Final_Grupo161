from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import CLAVE_JWT

ALGORITMO = "HS256"
DURACION_TOKEN = timedelta(hours=8)
LARGO_MAXIMO_BCRYPT = 72
HASH_FICTICIO = bcrypt.hashpw(b"ficticio", bcrypt.gensalt()).decode()


def verificar_contrasena(contrasena: str, hash_contrasena: str) -> bool:
    contrasena_en_bytes = contrasena.encode()
    if len(contrasena_en_bytes) > LARGO_MAXIMO_BCRYPT:
        return False
    return bcrypt.checkpw(contrasena_en_bytes, hash_contrasena.encode())


def crear_token(usuario_id: int) -> str:
    vencimiento = datetime.now(UTC) + DURACION_TOKEN
    return jwt.encode(
        {"sub": str(usuario_id), "exp": vencimiento}, CLAVE_JWT, algorithm=ALGORITMO
    )
