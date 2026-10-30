import threading
from datetime import date

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
    (4, "aux.unidad_a", 4),
    (5, "aux.unidad_b", 5),
    (6, "aux.unidad_c", 6),
]

BIENES = [
    (1, "ARMAMENTO", "Bersa", "TPR9", "BT-1", 4, None, 1),
    (2, "CHALECO", "FM S.A.", "RB3", "FM-1", 4, None, 1),
    (3, "ARMAMENTO", "Bersa", "TPR9", "BT-2", 4, 1, None),
    (4, "ARMAMENTO", "Glock", "17", "GL-1", 1, None, 4),
]

INSERTAR_MOVIMIENTO = (
    "INSERT INTO movimiento (id, tipo, estado, estado_revision, numero_acta, "
    "fecha_hecho, usuario_id, unidad_registrante_id, unidad_origen_id, "
    "oficial_origen_id, unidad_destino_id, oficial_destino_id) "
    "VALUES (:id, :tipo, 'PENDIENTE', :estado_revision, :numero_acta, CURDATE(), "
    ":usuario_id, :origen, :origen, :oficial, :destino, :oficial)"
)

INSERTAR_RENGLON = (
    "INSERT INTO movimiento_bien (movimiento_id, bien_id, ubicacion_origen_id) "
    "VALUES (:movimiento_id, :bien_id, :ubicacion_id)"
)

ACEPTAR = {
    "resultado": "ACEPTADO",
    "ubicaciones": [
        {"bien_id": 1, "ubicacion_id": 3},
        {"bien_id": 2, "ubicacion_id": 3},
    ],
}

RECHAZAR = {
    "resultado": "RECHAZADO",
    "motivo_rechazo": "Llegó un solo chaleco y el acta dice dos",
}


@pytest.fixture
def acta_pendiente():
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
                "(3, 5, 'Sala de Armas'), (4, 1, 'Sala de Armas'), "
                "(5, 2, 'Depósito')"
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
                "VALUES (:id, :tipo_bien, :marca, :modelo, :serie, "
                ":unidad_id, :oficial_id, :ubicacion_id)"
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
                ) in BIENES
            ],
        )
        insertar_movimiento(conexion, 1, "ENTREGA", "PENDIENTE", 4, 5)
        conexion.execute(
            text(INSERTAR_RENGLON),
            [
                {"movimiento_id": 1, "bien_id": 1, "ubicacion_id": 1},
                {"movimiento_id": 1, "bien_id": 2, "ubicacion_id": 1},
            ],
        )


def insertar_movimiento(
    conexion, id, tipo, estado_revision, origen, destino, oficial=None
):
    conexion.execute(
        text(INSERTAR_MOVIMIENTO),
        {
            "id": id,
            "tipo": tipo,
            "estado_revision": estado_revision,
            "numero_acta": f"{id:04d}/2026",
            "usuario_id": origen,
            "origen": origen,
            "destino": destino,
            "oficial": oficial,
        },
    )


def con_token(usuario_id):
    return {"Authorization": f"Bearer {crear_token(usuario_id)}"}


def recibir(client, recepcion, movimiento_id=1, usuario_id=5):
    return client.post(
        f"/api/movimientos/{movimiento_id}/recepcion",
        json=recepcion,
        headers=con_token(usuario_id),
    )


def consultar(sql):
    with engine.connect() as conexion:
        return conexion.execute(text(sql)).all()


def tenencia_de_los_bienes():
    return consultar(
        "SELECT id, unidad_id, ubicacion_id FROM bien WHERE id IN (1, 2) ORDER BY id"
    )


def test_la_unidad_de_destino_ve_las_actas_por_recibir(client, acta_pendiente):
    acta = client.get("/api/movimientos/1", headers=con_token(5)).json()

    respuesta = client.get("/api/movimientos/por-recibir", headers=con_token(5))

    assert respuesta.status_code == 200
    assert respuesta.json() == [acta]
    assert [bien["bien_id"] for bien in acta["bienes"]] == [1, 2]


def test_el_origen_no_tiene_actas_por_recibir(client, acta_pendiente):
    respuesta = client.get("/api/movimientos/por-recibir", headers=con_token(4))

    assert respuesta.json() == []


def test_las_ubicaciones_son_las_de_la_unidad_del_usuario(client, acta_pendiente):
    respuesta = client.get("/api/ubicaciones", headers=con_token(4))

    assert respuesta.status_code == 200
    assert respuesta.json() == [
        {"id": 2, "nombre": "Playón"},
        {"id": 1, "nombre": "Sala de Armas"},
    ]


def test_al_aceptar_los_bienes_pasan_al_destino_en_la_ubicacion_indicada(
    client, acta_pendiente
):
    respuesta = recibir(client, ACEPTAR)

    assert respuesta.status_code == 200
    acta = respuesta.json()
    assert acta["estado"] == "APLICADO"
    assert [renglon["ubicacion_destino"] for renglon in acta["bienes"]] == [
        "Sala de Armas",
        "Sala de Armas",
    ]
    assert tenencia_de_los_bienes() == [(1, 5, 3), (2, 5, 3)]
    assert consultar("SELECT resultado, usuario_id FROM recepcion") == [("ACEPTADO", 5)]


@pytest.mark.parametrize(
    "ubicaciones",
    [
        [{"bien_id": 1, "ubicacion_id": 3}],
        [{"bien_id": 1, "ubicacion_id": 3}, {"bien_id": 2, "ubicacion_id": 1}],
        [
            {"bien_id": 1, "ubicacion_id": 3},
            {"bien_id": 2, "ubicacion_id": 3},
            {"bien_id": 3, "ubicacion_id": 3},
        ],
    ],
    ids=["falta_una", "de_otra_unidad", "bien_de_otra_acta"],
)
def test_sin_una_ubicacion_propia_para_cada_bien_responde_422(
    client, acta_pendiente, ubicaciones
):
    respuesta = recibir(client, ACEPTAR | {"ubicaciones": ubicaciones})

    assert respuesta.status_code == 422
    assert tenencia_de_los_bienes() == [(1, 4, 1), (2, 4, 1)]
    assert consultar("SELECT estado FROM movimiento WHERE id = 1") == [("PENDIENTE",)]
    assert consultar("SELECT * FROM recepcion") == []


def test_al_rechazar_los_bienes_siguen_en_el_origen_y_libres(client, acta_pendiente):
    respuesta = recibir(client, RECHAZAR)

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "RECHAZADO"
    assert tenencia_de_los_bienes() == [(1, 4, 1), (2, 4, 1)]
    assert consultar("SELECT resultado, motivo_rechazo FROM recepcion") == [
        ("RECHAZADO", RECHAZAR["motivo_rechazo"])
    ]
    otra_entrega = client.post(
        "/api/movimientos/entregas",
        json={
            "unidad_destino_id": 5,
            "numero_acta": "0002/2026",
            "fecha_hecho": date.today().isoformat(),
            "bienes": [1, 2],
        },
        headers=con_token(4),
    )
    assert otra_entrega.status_code == 201


@pytest.mark.parametrize(
    "recepcion",
    [{"resultado": "RECHAZADO"}, RECHAZAR | {"motivo_rechazo": "  "}],
    ids=["sin_motivo", "motivo_en_blanco"],
)
def test_un_rechazo_sin_motivo_responde_422(client, acta_pendiente, recepcion):
    respuesta = recibir(client, recepcion)

    assert respuesta.status_code == 422
    assert consultar("SELECT * FROM recepcion") == []


@pytest.mark.parametrize("usuario_id", [4, 6], ids=["origen", "otra_unidad"])
def test_solo_la_unidad_de_destino_recibe_el_acta(client, acta_pendiente, usuario_id):
    respuesta = recibir(client, RECHAZAR, usuario_id=usuario_id)

    assert respuesta.status_code == 403
    assert respuesta.json() == {"detail": "Solo la unidad de destino recibe el acta"}


@pytest.mark.parametrize("primera", [ACEPTAR, RECHAZAR], ids=["aceptada", "rechazada"])
def test_un_acta_ya_recibida_responde_409(client, acta_pendiente, primera):
    recibir(client, primera)

    respuesta = recibir(client, RECHAZAR)

    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": "El acta no está pendiente de recepción"}


def test_un_traslado_no_se_recibe_como_una_entrega(client, acta_pendiente):
    with engine.begin() as conexion:
        insertar_movimiento(conexion, 2, "TRASLADO", "PENDIENTE", 4, 5, oficial=1)
        conexion.execute(
            text(INSERTAR_RENGLON),
            {"movimiento_id": 2, "bien_id": 3, "ubicacion_id": None},
        )

    respuesta = recibir(client, RECHAZAR, movimiento_id=2)

    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": "El acta no está pendiente de recepción"}
    por_recibir = client.get("/api/movimientos/por-recibir", headers=con_token(5))
    assert [acta["id"] for acta in por_recibir.json()] == [1]


def test_un_acta_inexistente_responde_404(client, acta_pendiente):
    assert recibir(client, RECHAZAR, movimiento_id=99).status_code == 404


def test_al_aceptar_cada_bien_toma_un_orden_nuevo_y_queda_para_revision(
    client, acta_pendiente
):
    recibir(client, ACEPTAR)

    assert consultar(
        "SELECT bien_id, orden FROM movimiento_bien WHERE movimiento_id = 1"
    ) == [(1, 1), (2, 1)]
    assert consultar(
        "SELECT unidad_revisora_id FROM v_bandeja_revision WHERE registro_id = 1"
    ) == [(2,)]


def test_lo_que_registra_direccion_no_queda_para_revision_al_aceptarlo(
    client, acta_pendiente
):
    with engine.begin() as conexion:
        insertar_movimiento(conexion, 2, "ENTREGA", "NO_APLICA", 1, 2)
        conexion.execute(
            text(INSERTAR_RENGLON),
            {"movimiento_id": 2, "bien_id": 4, "ubicacion_id": 4},
        )

    respuesta = recibir(
        client,
        {"resultado": "ACEPTADO", "ubicaciones": [{"bien_id": 4, "ubicacion_id": 5}]},
        movimiento_id=2,
        usuario_id=2,
    )

    assert respuesta.json()["estado"] == "APLICADO"
    assert consultar("SELECT orden FROM movimiento_bien WHERE movimiento_id = 2") == [
        (1,)
    ]
    assert consultar("SELECT * FROM v_bandeja_revision WHERE registro_id = 2") == []


def test_una_recepcion_espera_a_otra_en_curso_y_responde_409(client, acta_pendiente):
    # Sin el FOR UPDATE la API lee el acta pendiente y espera recién al insertar
    # la recepción, que termina en un error de clave duplicada.
    resultado = {}
    with Session(engine) as otra:
        otra.exec(text("SELECT id FROM bien WHERE id = 1 FOR UPDATE"))
        otra.exec(
            text(
                "INSERT INTO recepcion (movimiento_id, resultado, motivo_rechazo, "
                "usuario_id) VALUES (1, 'RECHAZADO', 'No llegó', 5)"
            )
        )
        otra.exec(text("UPDATE movimiento SET estado = 'RECHAZADO' WHERE id = 1"))
        # Abre la conexión que va a usar la API, así la espera es solo el bloqueo.
        client.get("/api/movimientos/1", headers=con_token(5))

        hilo = threading.Thread(
            target=lambda: resultado.update(respuesta=recibir(client, RECHAZAR))
        )
        hilo.start()
        hilo.join(timeout=2)
        assert hilo.is_alive()
        otra.commit()
    hilo.join(timeout=10)

    assert resultado["respuesta"].status_code == 409
    assert resultado["respuesta"].json() == {
        "detail": "El acta no está pendiente de recepción"
    }
