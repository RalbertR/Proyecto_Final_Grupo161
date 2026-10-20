from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
import pytest
from sqlmodel import text

from app.core.config import CLAVE_JWT
from app.core.database import engine

CONTRASENA = "secreta"

UNIDADES = [
    (1, "Dirección Logística", "DIRECCION", None),
    (2, "Unidad Regional Norte", "REGIONAL", 1),
    (3, "Unidad Regional Sur", "REGIONAL", 1),
    (4, "Unidad Operacional A", "OPERACIONAL", 2),
    (5, "Unidad Operacional B", "OPERACIONAL", 2),
    (6, "Unidad Operacional C", "OPERACIONAL", 3),
]

USUARIOS = [
    (1, "logistico.direccion", 1, True),
    (2, "logistico.regional_norte", 2, True),
    (3, "logistico.regional_sur", 3, True),
    (4, "aux.unidad_a", 4, True),
    (5, "aux.unidad_b", 5, True),
    (6, "aux.unidad_c", 6, True),
    (7, "aux.inactivo", 5, False),
]


@pytest.fixture
def organizacion():
    hash_contrasena = bcrypt.hashpw(
        CONTRASENA.encode(), bcrypt.gensalt(rounds=4)
    ).decode()
    with engine.begin() as conexion:
        conexion.execute(
            text(
                "INSERT INTO unidad (id, nombre, nivel, unidad_superior_id) "
                "VALUES (:id, :nombre, :nivel, :superior)"
            ),
            [
                {"id": id, "nombre": nombre, "nivel": nivel, "superior": superior}
                for id, nombre, nivel, superior in UNIDADES
            ],
        )
        conexion.execute(
            text(
                "INSERT INTO usuario "
                "(id, nombre_usuario, hash_contrasena, unidad_id, activo) "
                "VALUES (:id, :nombre, :hash, :unidad_id, :activo)"
            ),
            [
                {
                    "id": id,
                    "nombre": nombre,
                    "hash": hash_contrasena,
                    "unidad_id": unidad_id,
                    "activo": activo,
                }
                for id, nombre, unidad_id, activo in USUARIOS
            ],
        )


def iniciar_sesion(client, nombre_usuario, contrasena=CONTRASENA):
    return client.post(
        "/api/auth/login",
        data={"username": nombre_usuario, "password": contrasena},
    )


def test_login_correcto_devuelve_el_token_y_los_datos_del_usuario(client, organizacion):
    respuesta = iniciar_sesion(client, "aux.unidad_a")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["usuario"] == {
        "id": 4,
        "nombre_usuario": "aux.unidad_a",
        "unidad": {"id": 4, "nombre": "Unidad Operacional A", "nivel": "OPERACIONAL"},
    }


def test_el_token_identifica_al_usuario_y_vence_a_las_8_horas(client, organizacion):
    respuesta = iniciar_sesion(client, "aux.unidad_a")

    datos = jwt.decode(
        respuesta.json()["access_token"], CLAVE_JWT, algorithms=["HS256"]
    )
    vencimiento = datetime.fromtimestamp(datos["exp"], UTC)
    esperado = datetime.now(UTC) + timedelta(hours=8)
    assert datos["sub"] == "4"
    assert abs(vencimiento - esperado) < timedelta(minutes=1)


@pytest.mark.parametrize(
    "nombre_usuario, contrasena",
    [
        ("no.existe", CONTRASENA),
        ("aux.unidad_a", "incorrecta"),
        ("aux.inactivo", CONTRASENA),
        ("aux.unidad_a", "x" * 73),
    ],
    ids=["inexistente", "contrasena_incorrecta", "inactivo", "mas_de_72_bytes"],
)
def test_login_rechazado_responde_401_con_el_mismo_mensaje(
    client, organizacion, nombre_usuario, contrasena
):
    respuesta = iniciar_sesion(client, nombre_usuario, contrasena)

    assert respuesta.status_code == 401
    assert respuesta.json() == {"detail": "Usuario o contraseña incorrectos"}
