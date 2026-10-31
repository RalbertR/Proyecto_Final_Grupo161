import threading
from datetime import date, timedelta

import pytest
from sqlmodel import Session, text

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
    (3, "logistico.regional_sur", 3),
    (4, "aux.unidad_a", 4),
    (5, "aux.unidad_b", 5),
    (6, "aux.unidad_c", 6),
]

BIENES = [
    (1, "ARMAMENTO", "Bersa", "TPR9", "BT-1", 4, None, 1, False),
    (2, "CHALECO", "FM S.A.", "RB3", "FM-1", 4, None, 1, False),
    (3, "ARMAMENTO", "Bersa", "TPR9", "BT-2", 4, 1, None, False),
    (4, "MOVIL", "Toyota", "Hilux", None, 4, None, 2, False),
    (5, "ARMAMENTO", "Bersa", "TPR9", "BT-3", 5, None, 3, False),
    (6, "ARMAMENTO", "Glock", "17", "GL-1", 1, None, 4, False),
    (7, "ARMAMENTO", "Bersa", "TPR9", "BT-4", 4, None, 1, False),
    (8, "ARMAMENTO", "Bersa", "TPR9", "BT-5", 4, None, None, True),
]

HOY = date.today().isoformat()

ENTREGA = {
    "unidad_destino_id": 5,
    "numero_acta": "0016/2026",
    "fecha_hecho": HOY,
    "descripcion": "Refuerzo de armamento para la Unidad Operacional B",
    "bienes": [1, 2],
}

ACTA_REGISTRADA = {
    "tipo": "ENTREGA",
    "estado": "PENDIENTE",
    "estado_revision": "PENDIENTE",
    "numero_acta": "0016/2026",
    "fecha_hecho": HOY,
    "descripcion": "Refuerzo de armamento para la Unidad Operacional B",
    "unidad_origen": {
        "id": 4,
        "nombre": "Unidad Operacional A",
        "nivel": "OPERACIONAL",
    },
    "unidad_destino": {
        "id": 5,
        "nombre": "Unidad Operacional B",
        "nivel": "OPERACIONAL",
    },
    "usuario": "aux.unidad_a",
    "bienes": [
        {
            "bien_id": 1,
            "tipo_bien": "ARMAMENTO",
            "identificacion": "BT-1",
            "marca": "Bersa",
            "modelo": "TPR9",
            "ubicacion_origen": "Sala de Armas",
            "ubicacion_destino": None,
        },
        {
            "bien_id": 2,
            "tipo_bien": "CHALECO",
            "identificacion": "FM-1",
            "marca": "FM S.A.",
            "modelo": "RB3",
            "ubicacion_origen": "Sala de Armas",
            "ubicacion_destino": None,
        },
    ],
    "revisiones": [],
}

INSERTAR_ENTREGA_PENDIENTE = (
    "INSERT INTO movimiento (id, tipo, estado, estado_revision, numero_acta, "
    "fecha_hecho, usuario_id, unidad_registrante_id, unidad_origen_id, "
    "unidad_destino_id) VALUES (:id, 'ENTREGA', 'PENDIENTE', 'PENDIENTE', "
    "'0015/2026', CURDATE(), 4, 4, 4, 5)"
)

INSERTAR_RENGLON = (
    "INSERT INTO movimiento_bien (movimiento_id, bien_id, ubicacion_origen_id) "
    "VALUES (:movimiento_id, :bien_id, 1)"
)


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
                "(1, 4, 'Sala de Armas'), (2, 4, 'Playón'), "
                "(3, 5, 'Sala de Armas'), (4, 1, 'Sala de Armas')"
            )
        )
        conexion.execute(
            text(
                "INSERT INTO oficial (id, legajo, apellido, nombre, unidad_id) "
                "VALUES (1, '10001', 'Gómez', 'Laura', 4)"
            )
        )
        conexion.execute(
            text(
                "INSERT INTO bien (id, tipo_bien, marca, modelo, numero_serie, "
                "unidad_id, oficial_id, ubicacion_id, de_baja) "
                "VALUES (:id, :tipo_bien, :marca, :modelo, :serie, "
                ":unidad_id, :oficial_id, :ubicacion_id, :de_baja)"
            ),
            [
                {
                    "id": id,
                    "tipo_bien": tipo_bien,
                    "marca": marca,
                    "modelo": modelo,
                    "serie": serie,
                    "unidad_id": unidad_id,
                    "oficial_id": oficial_id,
                    "ubicacion_id": ubicacion_id,
                    "de_baja": de_baja,
                }
                for (
                    id,
                    tipo_bien,
                    marca,
                    modelo,
                    serie,
                    unidad_id,
                    oficial_id,
                    ubicacion_id,
                    de_baja,
                ) in BIENES
            ],
        )
        conexion.execute(
            text("INSERT INTO tipo_vehiculo (id, nombre) VALUES (1, 'Camioneta')")
        )
        conexion.execute(
            text("INSERT INTO tipo_tarea (id, nombre) VALUES (1, 'Patrullaje')")
        )
        conexion.execute(
            text(
                "INSERT INTO movil (bien_id, patente, numero_interno, anio, "
                "tipo_vehiculo_id, tipo_tarea_id) "
                "VALUES (4, 'AF104XY', '101', 2022, 1, 1)"
            )
        )
        conexion.execute(text(INSERTAR_ENTREGA_PENDIENTE), {"id": 1})
        conexion.execute(text(INSERTAR_RENGLON), {"movimiento_id": 1, "bien_id": 7})


def con_token(usuario_id):
    return {"Authorization": f"Bearer {crear_token(usuario_id)}"}


def entregar(client, usuario_id=4, **cambios):
    return client.post(
        "/api/movimientos/entregas",
        json=ENTREGA | cambios,
        headers=con_token(usuario_id),
    )


def cantidad_de_actas():
    with engine.connect() as conexion:
        return conexion.execute(text("SELECT COUNT(*) FROM movimiento")).scalar_one()


def test_registra_la_entrega_pendiente_de_recepcion(client, unidades_con_bienes):
    respuesta = entregar(client)

    assert respuesta.status_code == 201
    acta = respuesta.json()
    assert acta.pop("id") == 2
    assert acta.pop("fecha_carga")
    assert acta == ACTA_REGISTRADA


def test_con_la_entrega_pendiente_los_bienes_siguen_en_el_origen_y_marcados(
    client, unidades_con_bienes
):
    entregar(client)

    inventario = client.get("/api/inventario", headers=con_token(4)).json()

    assert [
        (fila["bien_id"], fila["unidad_id"], fila["con_movimiento_pendiente"])
        for fila in inventario
        if fila["bien_id"] in (1, 2)
    ] == [(1, 4, True), (2, 4, True)]


def test_un_bien_que_ya_esta_en_un_acta_pendiente_responde_409(
    client, unidades_con_bienes
):
    respuesta = entregar(client, bienes=[1, 7])

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "detail": "Uno de los bienes ya tiene un movimiento pendiente"
    }
    assert cantidad_de_actas() == 1


@pytest.mark.parametrize("bien_id", [3, 8], ids=["asignado_a_un_oficial", "de_baja"])
def test_un_bien_que_no_esta_en_deposito_responde_409(
    client, unidades_con_bienes, bien_id
):
    respuesta = entregar(client, bienes=[1, bien_id])

    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": "Uno de los bienes no está en depósito"}


@pytest.mark.parametrize("bien_id", [5, 99], ids=["de_otra_unidad", "inexistente"])
def test_un_bien_que_no_es_de_la_unidad_responde_403(
    client, unidades_con_bienes, bien_id
):
    respuesta = entregar(client, bienes=[1, bien_id])

    assert respuesta.status_code == 403
    assert respuesta.json() == {"detail": "Uno de los bienes no pertenece a su unidad"}


def test_armamento_y_un_movil_en_la_misma_entrega_responde_422(
    client, unidades_con_bienes
):
    respuesta = entregar(client, bienes=[1, 4])

    assert respuesta.status_code == 422
    assert "una sola área" in respuesta.json()["detail"]
    assert cantidad_de_actas() == 1


@pytest.mark.parametrize(
    "cambios",
    [
        {"numero_acta": "16/2026"},
        {"fecha_hecho": (date.today() + timedelta(days=1)).isoformat()},
        {"unidad_destino_id": 4},
        {"unidad_destino_id": 99},
        {"bienes": []},
    ],
    ids=[
        "acta_sin_formato",
        "fecha_posterior_a_hoy",
        "destino_igual_al_origen",
        "destino_inexistente",
        "sin_bienes",
    ],
)
def test_una_entrega_con_datos_invalidos_responde_422(
    client, unidades_con_bienes, cambios
):
    respuesta = entregar(client, **cambios)

    assert respuesta.status_code == 422
    assert cantidad_de_actas() == 1


def test_la_entrega_de_direccion_no_queda_para_revision(client, unidades_con_bienes):
    respuesta = entregar(client, 1, unidad_destino_id=2, bienes=[6])

    assert respuesta.status_code == 201
    assert respuesta.json()["estado_revision"] == "NO_APLICA"


@pytest.mark.parametrize(
    "usuario_id",
    [4, 5, 2, 1],
    ids=["origen", "destino", "regional_de_ambas", "direccion"],
)
def test_el_acta_la_consultan_el_origen_el_destino_y_sus_superiores(
    client, unidades_con_bienes, usuario_id
):
    registrada = entregar(client).json()

    respuesta = client.get("/api/movimientos/2", headers=con_token(usuario_id))

    assert respuesta.status_code == 200
    assert respuesta.json() == registrada


@pytest.mark.parametrize(
    "usuario_id", [6, 3], ids=["otra_operacional", "otra_regional"]
)
def test_el_acta_no_la_consulta_una_unidad_ajena(
    client, unidades_con_bienes, usuario_id
):
    respuesta = client.get("/api/movimientos/1", headers=con_token(usuario_id))

    assert respuesta.status_code == 403
    assert respuesta.json() == {"detail": "No tiene acceso a ese movimiento"}


def test_un_acta_inexistente_responde_404(client, unidades_con_bienes):
    respuesta = client.get("/api/movimientos/99", headers=con_token(4))

    assert respuesta.status_code == 404


def test_una_entrega_espera_a_otra_en_curso_con_el_mismo_bien_y_responde_409(
    client, unidades_con_bienes
):
    # Sin el FOR UPDATE la API igual espera, pero al insertar el renglón, y la
    # rechaza el trigger con su mensaje. Con el bloqueo espera antes de validar
    # y responde con el mensaje que muestra la pantalla (#28).
    resultado = {}
    with Session(engine) as otra:
        otra.exec(text(INSERTAR_ENTREGA_PENDIENTE).bindparams(id=2))
        otra.exec(text(INSERTAR_RENGLON).bindparams(movimiento_id=2, bien_id=1))
        # Abre la conexión que va a usar la API, así la espera es solo el bloqueo.
        client.get("/api/movimientos/1", headers=con_token(4))

        hilo = threading.Thread(
            target=lambda: resultado.update(respuesta=entregar(client))
        )
        hilo.start()
        hilo.join(timeout=2)
        assert hilo.is_alive()
        otra.commit()
    hilo.join(timeout=10)

    assert resultado["respuesta"].status_code == 409
    assert resultado["respuesta"].json() == {
        "detail": "Uno de los bienes ya tiene un movimiento pendiente"
    }
    assert cantidad_de_actas() == 2
