import pytest
from sqlmodel import text

from app.core.database import engine
from app.core.seguridad import crear_token

UNIDADES = [
    (1, "Dirección Logística", "DIRECCION", None),
    (2, "Unidad Regional Norte", "REGIONAL", 1),
    (3, "Unidad Regional Sur", "REGIONAL", 1),
    (4, "Unidad Operacional A", "OPERACIONAL", 2),
    (5, "Unidad Operacional B", "OPERACIONAL", 2),
    (6, "Unidad Operacional C", "OPERACIONAL", 3),
]

USUARIOS = [
    (1, "logistico.direccion", 1),
    (2, "logistico.regional_norte", 2),
    (4, "aux.unidad_a", 4),
]


@pytest.fixture
def organizacion():
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
                "INSERT INTO usuario (id, nombre_usuario, hash_contrasena, unidad_id) "
                "VALUES (:id, :nombre, 'x', :unidad_id)"
            ),
            [
                {"id": id, "nombre": nombre, "unidad_id": unidad_id}
                for id, nombre, unidad_id in USUARIOS
            ],
        )


def pedir_unidades(client, usuario_id, ruta="/api/unidades"):
    return client.get(
        ruta, headers={"Authorization": f"Bearer {crear_token(usuario_id)}"}
    )


def test_la_regional_recibe_su_unidad_y_sus_operacionales(client, organizacion):
    respuesta = pedir_unidades(client, 2)

    assert respuesta.status_code == 200
    assert respuesta.json() == [
        {"id": 2, "nombre": "Unidad Regional Norte", "nivel": "REGIONAL"},
        {"id": 4, "nombre": "Unidad Operacional A", "nivel": "OPERACIONAL"},
        {"id": 5, "nombre": "Unidad Operacional B", "nivel": "OPERACIONAL"},
    ]


@pytest.mark.parametrize(
    "usuario_id, unidades_esperadas",
    [(1, [1, 2, 3, 4, 5, 6]), (4, [4])],
    ids=["direccion", "operacional"],
)
def test_cada_nivel_recibe_las_unidades_de_su_alcance(
    client, organizacion, usuario_id, unidades_esperadas
):
    respuesta = pedir_unidades(client, usuario_id)

    assert [unidad["id"] for unidad in respuesta.json()] == unidades_esperadas


def test_los_destinos_son_todas_las_unidades_menos_la_propia(client, organizacion):
    respuesta = pedir_unidades(client, 4, "/api/unidades/destinos")

    assert respuesta.status_code == 200
    assert respuesta.json() == [
        {"id": 1, "nombre": "Dirección Logística", "nivel": "DIRECCION"},
        {"id": 2, "nombre": "Unidad Regional Norte", "nivel": "REGIONAL"},
        {"id": 3, "nombre": "Unidad Regional Sur", "nivel": "REGIONAL"},
        {"id": 5, "nombre": "Unidad Operacional B", "nivel": "OPERACIONAL"},
        {"id": 6, "nombre": "Unidad Operacional C", "nivel": "OPERACIONAL"},
    ]


def test_sin_sesion_responde_401(client, organizacion):
    respuesta = client.get("/api/unidades")

    assert respuesta.status_code == 401
    assert respuesta.json() == {"detail": "Sesión no válida o vencida"}
