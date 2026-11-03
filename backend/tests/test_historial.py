from datetime import date, timedelta

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
    (2, "logistico.regional_norte", 2),
    (4, "aux.unidad_a", 4),
    (5, "aux.unidad_b", 5),
    (6, "aux.unidad_c", 6),
]

HOY = date.today().isoformat()

# Días antes de hoy, para no depender de la zona horaria de la base.
AYER = (date.today() - timedelta(days=1)).isoformat()

DESCRIPCION = "Refuerzo de armamento para la Unidad Operacional B"

BIEN = {
    "id": 1,
    "tipo_bien": "ARMAMENTO",
    "identificacion": "BT-1",
    "marca": "Bersa",
    "modelo": "TPR9",
    "unidad": "Unidad Operacional A",
}


@pytest.fixture
def bien_de_a():
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
                "(1, 4, 'Sala de Armas'), (2, 5, 'Sala de Armas')"
            )
        )
        conexion.execute(
            text(
                "INSERT INTO bien (id, tipo_bien, marca, modelo, numero_serie, "
                "unidad_id, ubicacion_id) "
                "VALUES (1, 'ARMAMENTO', 'Bersa', 'TPR9', 'BT-1', 4, 1)"
            )
        )


def con_token(usuario_id):
    return {"Authorization": f"Bearer {crear_token(usuario_id)}"}


def entregar(client, usuario_id, destino, numero_acta, fecha_hecho=HOY):
    respuesta = client.post(
        "/api/movimientos/entregas",
        json={
            "unidad_destino_id": destino,
            "numero_acta": numero_acta,
            "fecha_hecho": fecha_hecho,
            "descripcion": DESCRIPCION,
            "bienes": [1],
        },
        headers=con_token(usuario_id),
    )
    assert respuesta.status_code == 201
    return respuesta.json()["id"]


def recibir(client, acta_id, usuario_id, ubicacion_id):
    respuesta = client.post(
        f"/api/movimientos/{acta_id}/recepcion",
        json={
            "resultado": "ACEPTADO",
            "ubicaciones": [{"bien_id": 1, "ubicacion_id": ubicacion_id}],
        },
        headers=con_token(usuario_id),
    )
    assert respuesta.status_code == 200


def rechazar(client, acta_id, usuario_id):
    respuesta = client.post(
        f"/api/movimientos/{acta_id}/recepcion",
        json={"resultado": "RECHAZADO", "motivo_rechazo": "No llegó el arma"},
        headers=con_token(usuario_id),
    )
    assert respuesta.status_code == 200


def historial(client, usuario_id, bien_id=1):
    return client.get(f"/api/bienes/{bien_id}/historial", headers=con_token(usuario_id))


def test_el_historial_trae_los_movimientos_en_el_orden_en_que_se_aplicaron(
    client, bien_de_a
):
    ida = entregar(client, 4, 5, "0016/2026")
    recibir(client, ida, 5, 2)
    # La vuelta tiene una fecha del hecho anterior: manda el orden de aplicación.
    vuelta = entregar(client, 5, 4, "0017/2026", fecha_hecho=AYER)
    recibir(client, vuelta, 4, 1)

    respuesta = historial(client, 4)

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "bien": BIEN,
        "eventos": [
            {
                "registro": "MOVIMIENTO",
                "registro_id": ida,
                "orden": 1,
                "evento": "ENTREGA",
                "fecha": HOY,
                "numero_acta": "0016/2026",
                "estado": "APLICADO",
                "estado_revision": "PENDIENTE",
                "origen": "Unidad Operacional A, Sala de Armas",
                "destino": "Unidad Operacional B, Sala de Armas",
                "detalle": DESCRIPCION,
            },
            {
                "registro": "MOVIMIENTO",
                "registro_id": vuelta,
                "orden": 2,
                "evento": "ENTREGA",
                "fecha": AYER,
                "numero_acta": "0017/2026",
                "estado": "APLICADO",
                "estado_revision": "PENDIENTE",
                "origen": "Unidad Operacional B, Sala de Armas",
                "destino": "Unidad Operacional A, Sala de Armas",
                "detalle": DESCRIPCION,
            },
        ],
    }


def test_un_movimiento_rectificado_muestra_la_ultima_version(client, bien_de_a):
    acta_id = entregar(client, 4, 5, "0016/2026")
    recibir(client, acta_id, 5, 2)
    for numero_acta, descripcion in [
        ("0018/2026", "Primera corrección"),
        ("0019/2026", "Segunda corrección"),
    ]:
        respuesta = client.post(
            f"/api/movimientos/{acta_id}/rectificaciones",
            json={
                "fecha_hecho": AYER,
                "numero_acta": numero_acta,
                "descripcion": descripcion,
                "motivo": "Se corrige según el acta firmada",
            },
            headers=con_token(4),
        )
        assert respuesta.status_code == 201

    [evento] = historial(client, 5).json()["eventos"]

    assert (evento["fecha"], evento["numero_acta"], evento["detalle"]) == (
        AYER,
        "0019/2026",
        "Segunda corrección",
    )


def test_las_actas_rechazadas_y_pendientes_aparecen_por_fecha_de_carga(
    client, bien_de_a
):
    rechazada = entregar(client, 4, 5, "0016/2026")
    rechazar(client, rechazada, 5)
    pendiente = entregar(client, 4, 5, "0017/2026")

    eventos = historial(client, 4).json()["eventos"]

    assert [
        (evento["registro_id"], evento["orden"], evento["estado"], evento["destino"])
        for evento in eventos
    ] == [
        (rechazada, None, "RECHAZADO", "Unidad Operacional B"),
        (pendiente, None, "PENDIENTE", "Unidad Operacional B"),
    ]


def test_un_usuario_de_otra_regional_no_ve_el_historial(client, bien_de_a):
    assert historial(client, 6).status_code == 403


def test_el_historial_de_un_bien_que_no_existe_responde_404(client, bien_de_a):
    assert historial(client, 4, bien_id=99).status_code == 404
