import threading
from datetime import date

import pytest
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, text

from app.core.database import engine
from app.core.seguridad import crear_token

HOY = date.today().isoformat()

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
    (5, "aux.unidad_b", 5),
    (6, "aux.unidad_c", 6),
]

# id, tipo, serie, unidad, oficial, ubicación
BIENES = [
    (1, "ARMAMENTO", "BT-1", 4, None, 1),
    (2, "CHALECO", "FM-1", 4, None, 1),
    (3, "ARMAMENTO", "BT-2", 4, None, 2),
    (4, "ARMAMENTO", "BT-3", 4, 1, None),
    (5, "ARMAMENTO", "BT-4", 5, None, 3),
    (6, "EQUIPO_COMUNICACIONES", "EQ-1", 4, None, 2),
]

ENTREGA = {
    "unidad_destino_id": 5,
    "numero_acta": "0001/2026",
    "fecha_hecho": HOY,
    "bienes": [1, 2],
}

DEVOLVER = {
    "resultado": "DEVUELTO",
    "motivo": "El acta dice BT-1 y llegó BT-2",
    "bienes_con_novedad": [1],
}

CORREGIDA = ENTREGA | {
    "numero_acta": "0002/2026",
    "descripcion": "Corregida",
    "bienes": [2, 3],
}


@pytest.fixture
def organizacion():
    with engine.begin() as conexion:
        conexion.execute(
            text(
                "INSERT INTO unidad (id, nombre, nivel, unidad_superior_id) "
                "VALUES (:id, :nombre, :nivel, :superior)"
            ),
            [
                {"id": i, "nombre": n, "nivel": nivel, "superior": s}
                for i, n, nivel, s in UNIDADES
            ],
        )
        conexion.execute(
            text(
                "INSERT INTO usuario (id, nombre_usuario, hash_contrasena, unidad_id) "
                "VALUES (:id, :nombre, 'x', :unidad_id)"
            ),
            [{"id": i, "nombre": n, "unidad_id": u} for i, n, u in USUARIOS],
        )
        conexion.execute(
            text(
                "INSERT INTO ubicacion (id, unidad_id, nombre) VALUES "
                "(1, 4, 'Sala de Armas'), (2, 4, 'Playón'), (3, 5, 'Sala de Armas')"
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
                "unidad_id, oficial_id, ubicacion_id) "
                "VALUES (:id, :tipo, 'Marca', 'Modelo', :serie, :unidad, "
                ":oficial, :ubicacion)"
            ),
            [
                {
                    "id": i,
                    "tipo": t,
                    "serie": s,
                    "unidad": u,
                    "oficial": o,
                    "ubicacion": ub,
                }
                for i, t, s, u, o, ub in BIENES
            ],
        )


def con_token(usuario_id):
    return {"Authorization": f"Bearer {crear_token(usuario_id)}"}


def consultar(sql):
    with engine.connect() as conexion:
        return conexion.execute(text(sql)).all()


def entregar(client, cuerpo=ENTREGA, usuario_id=4):
    return client.post(
        "/api/movimientos/entregas", json=cuerpo, headers=con_token(usuario_id)
    )


def devolver(client, cuerpo=DEVOLVER, movimiento_id=1, usuario_id=5):
    return client.post(
        f"/api/movimientos/{movimiento_id}/recepcion",
        json=cuerpo,
        headers=con_token(usuario_id),
    )


def corregir(client, cuerpo=CORREGIDA, movimiento_id=1, usuario_id=4):
    return client.put(
        f"/api/movimientos/{movimiento_id}", json=cuerpo, headers=con_token(usuario_id)
    )


def desistir(
    client, motivo="Se mandó a la unidad equivocada", movimiento_id=1, usuario_id=4
):
    return client.post(
        f"/api/movimientos/{movimiento_id}/desistimiento",
        json={"motivo": motivo},
        headers=con_token(usuario_id),
    )


def listar(client, ruta, usuario_id):
    return client.get(f"/api/movimientos/{ruta}", headers=con_token(usuario_id))


@pytest.fixture
def acta_devuelta(client, organizacion):
    assert entregar(client).status_code == 201
    assert devolver(client).status_code == 200


# --- Devolver ---


def test_al_devolver_el_acta_queda_devuelta_y_sale_de_por_recibir(client, organizacion):
    entregar(client)

    respuesta = devolver(client)

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "DEVUELTO"
    assert listar(client, "por-recibir", 5).json() == []
    assert consultar("SELECT resultado, motivo, usuario_id FROM recepcion") == [
        ("DEVUELTO", DEVOLVER["motivo"], 5)
    ]


def test_una_devolucion_deja_los_bienes_en_el_origen(client, organizacion):
    entregar(client)

    devolver(client)

    assert consultar(
        "SELECT id, unidad_id FROM bien WHERE id IN (1, 2) ORDER BY id"
    ) == [
        (1, 4),
        (2, 4),
    ]


def test_el_inventario_marca_pendientes_los_bienes_de_un_acta_devuelta(
    client, acta_devuelta
):
    inventario = client.get("/api/inventario", headers=con_token(4)).json()

    assert sorted(
        (fila["bien_id"], fila["con_movimiento_pendiente"])
        for fila in inventario
        if fila["bien_id"] in (1, 2, 3)
    ) == [(1, True), (2, True), (3, False)]


def test_la_ficha_del_bien_marca_pendiente_un_bien_de_un_acta_devuelta(
    client, acta_devuelta
):
    ficha = client.get("/api/bienes/1/historial", headers=con_token(4)).json()

    assert ficha["bien"]["con_movimiento_pendiente"] is True
    assert ficha["eventos"][0]["estado"] == "DEVUELTO"


def test_un_bien_de_un_acta_devuelta_no_entra_en_otra_entrega(client, acta_devuelta):
    respuesta = entregar(client, ENTREGA | {"numero_acta": "0003/2026", "bienes": [1]})

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "detail": "Uno de los bienes ya tiene un movimiento pendiente"
    }


def test_el_trigger_no_deja_insertar_un_bien_de_un_acta_devuelta_en_otra(
    client, acta_devuelta
):
    with engine.begin() as conexion:
        conexion.execute(
            text(
                "INSERT INTO movimiento (id, tipo, estado, estado_revision, "
                "numero_acta, fecha_hecho, usuario_id, unidad_registrante_id, "
                "unidad_origen_id, unidad_destino_id) VALUES (2, 'ENTREGA', "
                "'PENDIENTE', 'PENDIENTE', '0009/2026', CURDATE(), 4, 4, 4, 6)"
            )
        )
    with (
        pytest.raises(OperationalError, match="no admite otro"),
        engine.begin() as conexion,
    ):
        conexion.execute(
            text(
                "INSERT INTO movimiento_bien (movimiento_id, bien_id, "
                "ubicacion_origen_id) VALUES (2, 1, 1)"
            )
        )


def test_el_origen_ve_el_acta_devuelta_con_el_motivo_y_las_novedades(
    client, acta_devuelta
):
    respuesta = listar(client, "devueltas", 4)

    assert respuesta.status_code == 200
    (acta,) = respuesta.json()
    assert acta["id"] == 1
    assert acta["estado"] == "DEVUELTO"
    assert acta["recepciones"][0]["motivo"] == DEVOLVER["motivo"]
    assert acta["recepciones"][0]["bienes_con_novedad"] == [1]


@pytest.mark.parametrize("usuario_id", [5, 6], ids=["destino", "otra_unidad"])
def test_las_devueltas_son_solo_las_de_la_unidad_del_origen(
    client, acta_devuelta, usuario_id
):
    assert listar(client, "devueltas", usuario_id).json() == []


@pytest.mark.parametrize(
    "recepcion",
    [{"resultado": "DEVUELTO"}, DEVOLVER | {"motivo": "  "}],
    ids=["sin_motivo", "motivo_en_blanco"],
)
def test_una_devolucion_sin_motivo_responde_422(client, organizacion, recepcion):
    entregar(client)

    respuesta = devolver(client, recepcion)

    assert respuesta.status_code == 422
    assert consultar("SELECT * FROM recepcion") == []
    assert consultar("SELECT estado FROM movimiento WHERE id = 1") == [("PENDIENTE",)]


def test_una_novedad_de_un_bien_que_no_esta_en_el_acta_responde_422(
    client, organizacion
):
    entregar(client)

    respuesta = devolver(client, DEVOLVER | {"bienes_con_novedad": [3]})

    assert respuesta.status_code == 422
    assert respuesta.json() == {
        "detail": "Las novedades tienen que ser de bienes del acta"
    }
    assert consultar("SELECT * FROM recepcion") == []


def test_una_devolucion_puede_no_tener_bienes_con_novedad(client, organizacion):
    entregar(client)

    respuesta = devolver(client, DEVOLVER | {"bienes_con_novedad": []})

    assert respuesta.status_code == 200
    assert consultar("SELECT * FROM recepcion_novedad") == []


def test_el_destino_ya_no_rechaza_el_acta(client, organizacion):
    entregar(client)

    respuesta = devolver(
        client, {"resultado": "RECHAZADO", "motivo_rechazo": "No coincide"}
    )

    assert respuesta.status_code == 422
    assert consultar("SELECT estado FROM movimiento WHERE id = 1") == [("PENDIENTE",)]


@pytest.mark.parametrize(
    "cuerpo", [DEVOLVER, {"resultado": "ACEPTADO", "ubicaciones": []}]
)
def test_el_destino_no_recibe_ni_devuelve_un_acta_devuelta(
    client, acta_devuelta, cuerpo
):
    respuesta = devolver(client, cuerpo)

    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": "El acta no está pendiente de recepción"}


# --- Corregir y reenviar ---


def test_al_corregir_el_acta_vuelve_a_quedar_pendiente_en_el_destino(
    client, acta_devuelta
):
    respuesta = corregir(client)

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "PENDIENTE"
    assert [a["id"] for a in listar(client, "por-recibir", 5).json()] == [1]
    assert listar(client, "devueltas", 4).json() == []


def test_al_corregir_se_guarda_una_version_nueva_y_el_original_no_cambia(
    client, acta_devuelta
):
    acta = corregir(client).json()

    assert acta["version_vigente"] == 1
    assert acta["numero_acta"] == "0002/2026"
    assert acta["descripcion"] == "Corregida"
    assert [v["version"] for v in acta["versiones"]] == [0, 1]
    assert acta["versiones"][0]["numero_acta"] == "0001/2026"
    assert acta["versiones"][1]["motivo"] == DEVOLVER["motivo"]
    assert consultar("SELECT numero_acta FROM movimiento WHERE id = 1") == [
        ("0001/2026",)
    ]


def test_al_corregir_se_pueden_quitar_y_sumar_bienes(client, acta_devuelta):
    acta = corregir(client).json()

    assert [b["bien_id"] for b in acta["bienes"]] == [2, 3]
    inventario = client.get("/api/inventario", headers=con_token(4)).json()
    assert sorted(
        (f["bien_id"], f["con_movimiento_pendiente"])
        for f in inventario
        if f["bien_id"] in (1, 2, 3)
    ) == [(1, False), (2, True), (3, True)]


def test_al_corregir_se_puede_cambiar_el_destino(client, acta_devuelta):
    acta = corregir(client, CORREGIDA | {"unidad_destino_id": 6}).json()

    assert acta["unidad_destino"]["id"] == 6
    assert [a["id"] for a in listar(client, "por-recibir", 6).json()] == [1]
    assert listar(client, "por-recibir", 5).json() == []


def test_un_acta_corregida_se_puede_aceptar(client, acta_devuelta):
    corregir(client)

    respuesta = devolver(
        client,
        {
            "resultado": "ACEPTADO",
            "ubicaciones": [
                {"bien_id": 2, "ubicacion_id": 3},
                {"bien_id": 3, "ubicacion_id": 3},
            ],
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "APLICADO"
    assert respuesta.json()["motivo_rechazo"] is None
    assert consultar(
        "SELECT id, unidad_id FROM bien WHERE id IN (1, 2, 3) ORDER BY id"
    ) == [
        (1, 4),
        (2, 5),
        (3, 5),
    ]


def test_corregir_tiene_las_validaciones_de_la_entrega(client, acta_devuelta):
    casos = [
        (CORREGIDA | {"unidad_destino_id": 4}, 422),
        (CORREGIDA | {"unidad_destino_id": 99}, 422),
        (CORREGIDA | {"bienes": [2, 5]}, 403),
        (CORREGIDA | {"bienes": [2, 6]}, 422),
        (CORREGIDA | {"bienes": [2, 4]}, 409),
    ]
    for cuerpo, codigo in casos:
        assert corregir(client, cuerpo).status_code == codigo, cuerpo
    assert consultar("SELECT estado FROM movimiento WHERE id = 1") == [("DEVUELTO",)]
    assert consultar("SELECT bien_id FROM movimiento_bien ORDER BY bien_id") == [
        (1,),
        (2,),
    ]


@pytest.mark.parametrize(
    "cuerpo",
    [
        CORREGIDA | {"numero_acta": "2/2026"},
        CORREGIDA | {"fecha_hecho": "2999-01-01"},
        CORREGIDA | {"bienes": []},
    ],
    ids=["numero_de_acta", "fecha_futura", "sin_bienes"],
)
def test_corregir_valida_el_cuerpo_como_la_entrega(client, acta_devuelta, cuerpo):
    assert corregir(client, cuerpo).status_code == 422


def test_corregir_no_admite_un_bien_con_otro_movimiento_pendiente(
    client, acta_devuelta
):
    entregar(client, ENTREGA | {"numero_acta": "0003/2026", "bienes": [3]})

    respuesta = corregir(client)

    assert respuesta.status_code == 409


@pytest.mark.parametrize("usuario_id", [5, 6], ids=["destino", "otra_unidad"])
def test_solo_el_origen_corrige_el_acta(client, acta_devuelta, usuario_id):
    respuesta = corregir(client, usuario_id=usuario_id)

    assert respuesta.status_code == 403
    assert respuesta.json() == {"detail": "Solo la unidad de origen corrige el acta"}


def test_no_se_corrige_un_acta_que_no_esta_devuelta(client, organizacion):
    entregar(client)

    respuesta = corregir(client)

    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": "El acta no está devuelta"}


def test_corregir_un_acta_inexistente_responde_404(client, organizacion):
    assert corregir(client, movimiento_id=99).status_code == 404


# --- Desistir ---


def test_al_desistir_el_acta_queda_rechazada_y_los_bienes_libres(client, acta_devuelta):
    respuesta = desistir(client)

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "RECHAZADO"
    assert respuesta.json()["motivo_rechazo"] == "Se mandó a la unidad equivocada"
    assert listar(client, "devueltas", 4).json() == []
    otra = entregar(client, ENTREGA | {"numero_acta": "0003/2026"})
    assert otra.status_code == 201


def test_el_desistimiento_guarda_quien_lo_hizo(client, acta_devuelta):
    desistir(client)

    assert consultar(
        "SELECT resultado, motivo, usuario_id FROM recepcion ORDER BY id"
    ) == [
        ("DEVUELTO", DEVOLVER["motivo"], 5),
        ("RECHAZADO", "Se mandó a la unidad equivocada", 4),
    ]


@pytest.mark.parametrize("motivo", ["", "   "])
def test_un_desistimiento_sin_motivo_responde_422(client, acta_devuelta, motivo):
    assert desistir(client, motivo).status_code == 422
    assert consultar("SELECT estado FROM movimiento WHERE id = 1") == [("DEVUELTO",)]


@pytest.mark.parametrize("usuario_id", [5, 6], ids=["destino", "otra_unidad"])
def test_solo_el_origen_desiste_del_acta(client, acta_devuelta, usuario_id):
    respuesta = desistir(client, usuario_id=usuario_id)

    assert respuesta.status_code == 403
    assert respuesta.json() == {"detail": "Solo la unidad de origen desiste del acta"}


def test_no_se_desiste_de_un_acta_que_no_esta_devuelta(client, organizacion):
    entregar(client)

    respuesta = desistir(client)

    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": "El acta no está devuelta"}


def test_desistir_de_un_acta_inexistente_responde_404(client, organizacion):
    assert desistir(client, movimiento_id=99).status_code == 404


# --- Detalle ---


def test_el_detalle_muestra_cada_devolucion(client, acta_devuelta):
    corregir(client)
    devolver(
        client, DEVOLVER | {"motivo": "Sigue sin coincidir", "bienes_con_novedad": [2]}
    )

    acta = client.get("/api/movimientos/1", headers=con_token(4)).json()

    assert [
        (r["resultado"], r["motivo"], r["bienes_con_novedad"], r["usuario"])
        for r in acta["recepciones"]
    ] == [
        ("DEVUELTO", DEVOLVER["motivo"], [1], "aux.unidad_b"),
        ("DEVUELTO", "Sigue sin coincidir", [2], "aux.unidad_b"),
    ]
    assert all(r["fecha"] for r in acta["recepciones"])


def test_las_novedades_se_conservan_si_el_bien_sale_del_acta(client, acta_devuelta):
    corregir(client)

    acta = client.get("/api/movimientos/1", headers=con_token(5)).json()

    assert [b["bien_id"] for b in acta["bienes"]] == [2, 3]
    assert acta["recepciones"][0]["bienes_con_novedad"] == [1]


# --- Concurrencia ---


@pytest.mark.parametrize(
    "operacion",
    [
        lambda client: corregir(client),
        lambda client: desistir(client),
        lambda client: devolver(client),
    ],
    ids=["corregir", "desistir", "devolver"],
)
def test_una_operacion_espera_a_otra_en_curso_y_responde_409(
    client, acta_devuelta, operacion
):
    # Sin el FOR UPDATE la API lee el estado antes de que la otra operación
    # confirme y actúa sobre un acta que ya no está devuelta.
    resultado = {}
    with Session(engine) as otra:
        otra.exec(text("SELECT id FROM bien WHERE id IN (1, 2) ORDER BY id FOR UPDATE"))
        otra.exec(
            text(
                "INSERT INTO recepcion (movimiento_id, resultado, motivo, "
                "usuario_id) VALUES (1, 'RECHAZADO', 'Desistió', 4)"
            )
        )
        otra.exec(text("UPDATE movimiento SET estado = 'RECHAZADO' WHERE id = 1"))
        # Abre la conexión que va a usar la API, así la espera es solo el bloqueo.
        client.get("/api/movimientos/1", headers=con_token(4))

        hilo = threading.Thread(
            target=lambda: resultado.update(respuesta=operacion(client))
        )
        hilo.start()
        hilo.join(timeout=2)
        assert hilo.is_alive()
        otra.commit()
    hilo.join(timeout=10)

    assert resultado["respuesta"].status_code == 409
