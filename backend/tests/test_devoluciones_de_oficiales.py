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
]

USUARIOS = [
    (1, "logistico.direccion", 1),
    (2, "logistico.regional_norte", 2),
    (3, "logistico.regional_sur", 3),
    (4, "aux.unidad_a", 4),
    (5, "aux.unidad_b", 5),
]

# id, legajo, apellido, nombre, unidad, activo
OFICIALES = [
    (1, "50123", "Gómez", "Laura", 4, True),
    (2, "50124", "Acosta", "Pedro", 4, True),
    (3, "50125", "Baez", "Ana", 4, False),
    (4, "50126", "Ruiz", "Marta", 5, True),
    (5, "50127", "Sosa", "Luis", 1, True),
]

# id, tipo, serie, unidad, oficial, ubicación
BIENES = [
    (1, "ARMAMENTO", "BT-1", 4, 1, None),
    (2, "CHALECO", "FM-1", 4, 1, None),
    (3, "ARMAMENTO", "BT-2", 4, 2, None),
    (4, "MOVIL", None, 4, 1, None),
    (5, "ARMAMENTO", "BT-3", 4, None, 1),
    (6, "ARMAMENTO", "BT-4", 4, 1, None),
    (7, "ARMAMENTO", "GL-1", 1, 5, None),
    (8, "ARMAMENTO", "BT-5", 5, 4, None),
]

HOY = date.today().isoformat()

DEVOLUCION = {
    "oficial_id": 1,
    "numero_acta": "0018/2026",
    "fecha_hecho": HOY,
    "descripcion": "Devolución por licencia",
    "ubicaciones": [
        {"bien_id": 1, "ubicacion_id": 1},
        {"bien_id": 2, "ubicacion_id": 2},
    ],
}

GOMEZ = {"id": 1, "legajo": "50123", "nombre": "Gómez, Laura"}


@pytest.fixture
def oficiales_con_bienes():
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
                "(3, 1, 'Sala de Armas'), (4, 5, 'Sala de Armas')"
            )
        )
        conexion.execute(
            text(
                "INSERT INTO oficial (id, legajo, apellido, nombre, unidad_id, activo) "
                "VALUES (:id, :legajo, :apellido, :nombre, :unidad_id, :activo)"
            ),
            [
                {
                    "id": id,
                    "legajo": legajo,
                    "apellido": apellido,
                    "nombre": nombre,
                    "unidad_id": unidad_id,
                    "activo": activo,
                }
                for id, legajo, apellido, nombre, unidad_id, activo in OFICIALES
            ],
        )
        conexion.execute(
            text(
                "INSERT INTO bien (id, tipo_bien, marca, modelo, numero_serie, "
                "unidad_id, oficial_id, ubicacion_id) "
                "VALUES (:id, :tipo, 'Marca', 'Modelo', :serie, :unidad, "
                ":oficial, :ubicacion)"
            ),
            [
                {
                    "id": id,
                    "tipo": tipo,
                    "serie": serie,
                    "unidad": unidad,
                    "oficial": oficial,
                    "ubicacion": ubicacion,
                }
                for id, tipo, serie, unidad, oficial, ubicacion in BIENES
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


def con_token(usuario_id):
    return {"Authorization": f"Bearer {crear_token(usuario_id)}"}


def devolver(client, usuario_id=4, **cambios):
    return client.post(
        "/api/movimientos/devoluciones",
        json=DEVOLUCION | cambios,
        headers=con_token(usuario_id),
    )


def cantidad_de_actas():
    with engine.connect() as conexion:
        return conexion.execute(text("SELECT COUNT(*) FROM movimiento")).scalar_one()


def tenencia(bien_id):
    with engine.connect() as conexion:
        return (
            conexion.execute(
                text(
                    "SELECT unidad_id, oficial_id, ubicacion_id FROM bien WHERE id = :id"
                ),
                {"id": bien_id},
            )
            .mappings()
            .one()
        )


def con_traslado_pendiente_del_bien(bien_id):
    with engine.begin() as conexion:
        conexion.execute(
            text(
                "INSERT INTO movimiento (id, tipo, estado, estado_revision, "
                "numero_acta, fecha_hecho, usuario_id, unidad_registrante_id, "
                "unidad_origen_id, unidad_destino_id) VALUES (50, 'ENTREGA', "
                "'PENDIENTE', 'PENDIENTE', '0015/2026', CURDATE(), 4, 4, 4, 5)"
            )
        )
        conexion.execute(
            text(
                "INSERT INTO movimiento_bien (movimiento_id, bien_id, "
                "ubicacion_origen_id) VALUES (50, :bien_id, 1)"
            ),
            {"bien_id": bien_id},
        )


def test_registra_la_devolucion_aplicada_y_los_bienes_vuelven_al_deposito(
    client, oficiales_con_bienes
):
    respuesta = devolver(client)

    assert respuesta.status_code == 201
    acta = respuesta.json()
    assert acta["tipo"] == "ENTREGA"
    assert acta["estado"] == "APLICADO"
    assert acta["numero_acta"] == "0018/2026"
    assert acta["fecha_hecho"] == HOY
    assert acta["unidad_origen"]["id"] == 4
    assert acta["unidad_destino"]["id"] == 4
    assert acta["oficial_origen"] == GOMEZ
    assert acta["oficial_destino"] is None
    assert [
        (renglon["bien_id"], renglon["ubicacion_destino"]) for renglon in acta["bienes"]
    ] == [(1, "Sala de Armas"), (2, "Playón")]
    assert tenencia(1) == {"unidad_id": 4, "oficial_id": None, "ubicacion_id": 1}
    assert tenencia(2) == {"unidad_id": 4, "oficial_id": None, "ubicacion_id": 2}
    # Los demás bienes del oficial siguen con él.
    assert tenencia(6)["oficial_id"] == 1


def test_cada_bien_toma_un_orden_nuevo_y_el_acta_queda_para_la_revision_de_la_regional(
    client, oficiales_con_bienes
):
    # Se asigna primero a Gómez para que el bien ya tenga el orden 1.
    with engine.begin() as conexion:
        conexion.execute(
            text(
                "UPDATE bien SET oficial_id = NULL, ubicacion_id = 1 WHERE id IN (1, 2)"
            )
        )
    dotacion = client.post(
        "/api/movimientos/dotaciones",
        json={
            "oficial_id": 1,
            "numero_acta": "0017/2026",
            "fecha_hecho": HOY,
            "bienes": [1, 2],
        },
        headers=con_token(4),
    )
    assert dotacion.status_code == 201

    acta_id = devolver(client).json()["id"]

    for bien_id in (1, 2):
        historial = client.get(
            f"/api/bienes/{bien_id}/historial", headers=con_token(4)
        ).json()
        [_, evento] = historial["eventos"]
        assert (evento["registro_id"], evento["orden"]) == (acta_id, 2)
        assert evento["estado"] == "APLICADO"
        assert evento["estado_revision"] == "PENDIENTE"

    bandeja = client.get("/api/revisiones/bandeja", headers=con_token(2)).json()
    assert acta_id in [fila["registro_id"] for fila in bandeja]


def test_la_devolucion_de_direccion_no_queda_para_revision(
    client, oficiales_con_bienes
):
    respuesta = devolver(
        client,
        1,
        oficial_id=5,
        ubicaciones=[{"bien_id": 7, "ubicacion_id": 3}],
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["estado_revision"] == "NO_APLICA"
    assert tenencia(7) == {"unidad_id": 1, "oficial_id": None, "ubicacion_id": 3}


def test_el_detalle_del_acta_trae_el_oficial_de_origen(client, oficiales_con_bienes):
    acta_id = devolver(client).json()["id"]

    respuesta = client.get(f"/api/movimientos/{acta_id}", headers=con_token(4))

    assert respuesta.status_code == 200
    assert respuesta.json()["oficial_origen"] == GOMEZ


def test_un_bien_de_otro_oficial_responde_409(client, oficiales_con_bienes):
    respuesta = devolver(
        client,
        ubicaciones=[
            {"bien_id": 1, "ubicacion_id": 1},
            {"bien_id": 3, "ubicacion_id": 1},
        ],
    )

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "detail": "Uno de los bienes no está asignado a ese oficial"
    }
    assert cantidad_de_actas() == 0
    assert tenencia(1)["oficial_id"] == 1


def test_un_bien_en_deposito_responde_409(client, oficiales_con_bienes):
    respuesta = devolver(
        client,
        ubicaciones=[
            {"bien_id": 1, "ubicacion_id": 1},
            {"bien_id": 5, "ubicacion_id": 1},
        ],
    )

    assert respuesta.status_code == 409
    assert cantidad_de_actas() == 0


def test_un_bien_con_un_movimiento_pendiente_responde_409(client, oficiales_con_bienes):
    con_traslado_pendiente_del_bien(6)

    respuesta = devolver(
        client,
        ubicaciones=[
            {"bien_id": 1, "ubicacion_id": 1},
            {"bien_id": 6, "ubicacion_id": 1},
        ],
    )

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "detail": "Uno de los bienes ya tiene un movimiento pendiente"
    }
    assert cantidad_de_actas() == 1


@pytest.mark.parametrize(
    "ubicaciones",
    [
        [{"bien_id": 1, "ubicacion_id": 1}, {"bien_id": 2, "ubicacion_id": 4}],
        [{"bien_id": 1, "ubicacion_id": 1}, {"bien_id": 2, "ubicacion_id": 99}],
        [{"bien_id": 1, "ubicacion_id": 1}, {"bien_id": 2}],
        [{"bien_id": 1, "ubicacion_id": 1}, {"bien_id": 2, "ubicacion_id": None}],
        [{"bien_id": 1, "ubicacion_id": 1}, {"bien_id": 1, "ubicacion_id": 2}],
    ],
    ids=[
        "de_otra_unidad",
        "inexistente",
        "sin_ubicacion",
        "ubicacion_nula",
        "bien_repetido",
    ],
)
def test_una_ubicacion_que_falta_o_es_ajena_responde_422_y_ningun_bien_cambia(
    client, oficiales_con_bienes, ubicaciones
):
    respuesta = devolver(client, ubicaciones=ubicaciones)

    assert respuesta.status_code == 422
    assert cantidad_de_actas() == 0
    assert tenencia(1)["oficial_id"] == 1
    assert tenencia(2)["oficial_id"] == 1


@pytest.mark.parametrize(
    "cambios",
    [
        {
            "ubicaciones": [
                {"bien_id": 1, "ubicacion_id": 1},
                {"bien_id": 4, "ubicacion_id": 2},
            ]
        },
        {"numero_acta": "18/2026"},
        {"fecha_hecho": (date.today() + timedelta(days=1)).isoformat()},
        {"ubicaciones": []},
    ],
    ids=["dos_areas", "acta_sin_formato", "fecha_posterior_a_hoy", "sin_bienes"],
)
def test_una_devolucion_con_datos_invalidos_responde_422(
    client, oficiales_con_bienes, cambios
):
    respuesta = devolver(client, **cambios)

    assert respuesta.status_code == 422
    assert cantidad_de_actas() == 0
    assert tenencia(1)["oficial_id"] == 1


@pytest.mark.parametrize("bien_id", [8, 99], ids=["de_otra_unidad", "inexistente"])
def test_un_bien_que_no_es_de_la_unidad_responde_403(
    client, oficiales_con_bienes, bien_id
):
    respuesta = devolver(
        client,
        ubicaciones=[
            {"bien_id": 1, "ubicacion_id": 1},
            {"bien_id": bien_id, "ubicacion_id": 1},
        ],
    )

    assert respuesta.status_code == 403
    assert respuesta.json() == {"detail": "Uno de los bienes no pertenece a su unidad"}
    assert cantidad_de_actas() == 0


def test_un_usuario_de_otra_unidad_responde_403(client, oficiales_con_bienes):
    respuesta = devolver(client, 5)

    assert respuesta.status_code == 403
    assert cantidad_de_actas() == 0
    assert tenencia(1)["oficial_id"] == 1


def test_la_devolucion_se_pide_con_sesion(client, oficiales_con_bienes):
    respuesta = client.post("/api/movimientos/devoluciones", json=DEVOLUCION)

    assert respuesta.status_code == 401
