import threading
from concurrent.futures import ThreadPoolExecutor
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


def abrir_conexiones_en_el_pool(cantidad):
    conexiones = [engine.connect() for _ in range(cantidad)]
    for conexion in conexiones:
        conexion.close()


def en_simultaneo(*pedidos):
    abrir_conexiones_en_el_pool(len(pedidos))
    barrera = threading.Barrier(len(pedidos))

    def pedir(pedido):
        barrera.wait()
        return pedido()

    with ThreadPoolExecutor(len(pedidos)) as hilos:
        return list(hilos.map(pedir, pedidos, timeout=10))


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


def test_dos_entregas_simultaneas_del_mismo_bien_registran_una_sola(
    client, unidades_con_bienes
):
    respuestas = en_simultaneo(
        lambda: entregar(client, 4),
        lambda: entregar(client, 7, numero_acta="0002/2026"),
    )

    assert sorted(respuesta.status_code for respuesta in respuestas) == [201, 409]
    ganadora = next(r for r in respuestas if r.status_code == 201)
    rechazada = next(r for r in respuestas if r.status_code == 409)
    assert rechazada.json() == {
        "detail": "Uno de los bienes ya tiene un movimiento pendiente"
    }
    assert consultar("SELECT id, estado FROM movimiento") == [
        (ganadora.json()["id"], "PENDIENTE")
    ]
    assert consultar("SELECT bien_id FROM movimiento_bien ORDER BY bien_id") == [
        (1,),
        (2,),
    ]


def test_dos_recepciones_simultaneas_de_la_misma_acta_aplican_una_sola(
    client, unidades_con_bienes
):
    acta_id = entregar(client).json()["id"]

    respuestas = en_simultaneo(
        lambda: recibir(client, acta_id, 5),
        lambda: recibir(client, acta_id, 8),
    )

    assert sorted(respuesta.status_code for respuesta in respuestas) == [200, 409]
    rechazada = next(r for r in respuestas if r.status_code == 409)
    assert rechazada.json() == {"detail": "El acta no está pendiente de recepción"}
    assert consultar("SELECT COUNT(*) FROM recepcion") == [(1,)]
    assert consultar("SELECT bien_id, orden FROM movimiento_bien ORDER BY bien_id") == [
        (1, 1),
        (2, 1),
    ]
    assert consultar(
        "SELECT id, unidad_id, ubicacion_id FROM bien WHERE id IN (1, 2) ORDER BY id"
    ) == [(1, 5, 2), (2, 5, 3)]
