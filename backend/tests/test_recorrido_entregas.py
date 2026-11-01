from datetime import date

import pytest
from sqlmodel import text

from app.core.database import engine
from app.core.seguridad import crear_token

UNIDADES = [
    (1, "Dirección Logística", "DIRECCION", None),
    (2, "Unidad Regional Norte", "REGIONAL", 1),
    (4, "Unidad Operacional A", "OPERACIONAL", 2),
    (5, "Unidad Operacional B", "OPERACIONAL", 2),
]

USUARIOS = [
    (2, "logistico.regional_norte", 2),
    (4, "aux.unidad_a", 4),
    (5, "aux.unidad_b", 5),
    (7, "aux2.unidad_a", 4),
    (8, "aux2.unidad_b", 5),
]

BIENES = [
    (1, "ARMAMENTO", "Bersa", "TPR9", "BT-1"),
    (2, "CHALECO", "FM S.A.", "RB3", "FM-1"),
    (3, "ARMAMENTO", "Bersa", "TPR9", "BT-2"),
]

HOY = date.today().isoformat()

ENTREGA = {
    "unidad_destino_id": 5,
    "numero_acta": "0001/2026",
    "fecha_hecho": HOY,
    "descripcion": "Refuerzo de armamento para la Unidad Operacional B",
    "bienes": [1, 2],
}

ACEPTAR = {
    "resultado": "ACEPTADO",
    "ubicaciones": [
        {"bien_id": 1, "ubicacion_id": 2},
        {"bien_id": 2, "ubicacion_id": 3},
    ],
}


@pytest.fixture
def unidades_con_bienes():
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
        conexion.execute(
            text(
                "INSERT INTO ubicacion (id, unidad_id, nombre) VALUES "
                "(1, 4, 'Sala de Armas'), (2, 5, 'Sala de Armas'), (3, 5, 'Depósito')"
            )
        )
        conexion.execute(
            text(
                "INSERT INTO bien (id, tipo_bien, marca, modelo, numero_serie, "
                "unidad_id, ubicacion_id) "
                "VALUES (:id, :tipo_bien, :marca, :modelo, :serie, 4, 1)"
            ),
            [
                {
                    "id": id,
                    "tipo_bien": tipo_bien,
                    "marca": marca,
                    "modelo": modelo,
                    "serie": serie,
                }
                for id, tipo_bien, marca, modelo, serie in BIENES
            ],
        )


def con_token(usuario_id):
    return {"Authorization": f"Bearer {crear_token(usuario_id)}"}


def consultar(sql):
    with engine.connect() as conexion:
        return conexion.execute(text(sql)).all()


def entregar(client, usuario_id=4, **cambios):
    return client.post(
        "/api/movimientos/entregas",
        json=ENTREGA | cambios,
        headers=con_token(usuario_id),
    )


def recibir(client, movimiento_id, usuario_id=5):
    return client.post(
        f"/api/movimientos/{movimiento_id}/recepcion",
        json=ACEPTAR,
        headers=con_token(usuario_id),
    )


def revisar(client, movimiento_id, version, resultado="REVISADO", motivo=None):
    return client.post(
        f"/api/movimientos/{movimiento_id}/revisiones",
        json={
            "resultado": resultado,
            "version": version,
            "motivo_observacion": motivo,
        },
        headers=con_token(2),
    )


def bandeja(client):
    return client.get("/api/revisiones/bandeja", headers=con_token(2)).json()


def inventario(client, usuario_id):
    return client.get("/api/inventario", headers=con_token(usuario_id)).json()


def test_una_entrega_de_a_a_b_queda_recibida_revisada_y_en_el_historial(
    client, unidades_con_bienes
):
    registrada = entregar(client)
    assert registrada.status_code == 201
    acta_id = registrada.json()["id"]

    por_recibir = client.get("/api/movimientos/por-recibir", headers=con_token(5))
    assert [acta["id"] for acta in por_recibir.json()] == [acta_id]

    recibida = recibir(client, acta_id)
    assert recibida.status_code == 200
    assert recibida.json()["estado"] == "APLICADO"

    assert [
        (registro["registro_id"], registro["version"]) for registro in bandeja(client)
    ] == [(acta_id, 0)]
    assert revisar(client, acta_id, 0).status_code == 201
    assert bandeja(client) == []

    acta = client.get(f"/api/movimientos/{acta_id}", headers=con_token(4)).json()
    assert acta["estado_revision"] == "REVISADO"
    assert [renglon["ubicacion_destino"] for renglon in acta["bienes"]] == [
        "Sala de Armas",
        "Depósito",
    ]
    assert [
        (revision["resultado"], revision["version_revisada"])
        for revision in acta["revisiones"]
    ] == [("REVISADO", 0)]

    assert [fila["bien_id"] for fila in inventario(client, 4)] == [3]
    assert [
        (fila["bien_id"], fila["ubicacion"], fila["con_movimiento_pendiente"])
        for fila in inventario(client, 5)
    ] == [(1, "Sala de Armas", False), (2, "Depósito", False)]

    assert consultar(
        "SELECT bien_id, orden, evento, estado, estado_revision, unidad_origen_id, "
        "ubicacion_origen_id, unidad_destino_id, ubicacion_destino_id "
        "FROM v_historial_bien ORDER BY bien_id"
    ) == [
        (1, 1, "ENTREGA", "APLICADO", "REVISADO", 4, 1, 5, 2),
        (2, 1, "ENTREGA", "APLICADO", "REVISADO", 4, 1, 5, 3),
    ]
