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
    (3, "logistico.regional_sur", 3),
    (4, "aux.unidad_a", 4),
    (5, "aux.unidad_b", 5),
]

INSERTAR_ENTREGA = (
    "INSERT INTO movimiento (id, tipo, estado, estado_revision, numero_acta, "
    "fecha_hecho, descripcion, usuario_id, unidad_registrante_id, "
    "unidad_origen_id, unidad_destino_id) "
    "VALUES (:id, 'ENTREGA', :estado, :estado_revision, :numero_acta, CURDATE(), "
    ":descripcion, :usuario_id, :origen, :origen, :destino)"
)

DESCRIPCION = "Refuerzo de armamento para la Unidad Operacional B"

EN_LA_BANDEJA = {
    "registro": "MOVIMIENTO",
    "registro_id": 1,
    "evento": "ENTREGA",
    "fecha": date.today().isoformat(),
    "unidad_registrante": "Unidad Operacional A",
    "usuario": "aux.unidad_a",
    "detalle": DESCRIPCION,
    "version": 0,
}

REVISAR = {"resultado": "REVISADO", "version": 0}

OBSERVAR = {
    "resultado": "OBSERVADO",
    "motivo_observacion": "El acta firmada es del 28/10",
    "version": 0,
}


@pytest.fixture
def entrega_aplicada():
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
        insertar_entrega(conexion, 1, "APLICADO", "PENDIENTE", 4, 5)


def insertar_entrega(conexion, id, estado, estado_revision, origen, destino):
    conexion.execute(
        text(INSERTAR_ENTREGA),
        {
            "id": id,
            "estado": estado,
            "estado_revision": estado_revision,
            "numero_acta": f"{id:04d}/2026",
            "descripcion": DESCRIPCION,
            "usuario_id": origen,
            "origen": origen,
            "destino": destino,
        },
    )


def con_token(usuario_id):
    return {"Authorization": f"Bearer {crear_token(usuario_id)}"}


def bandeja(client, usuario_id=2):
    return client.get("/api/revisiones/bandeja", headers=con_token(usuario_id))


def revisar(client, revision, movimiento_id=1, usuario_id=2):
    return client.post(
        f"/api/movimientos/{movimiento_id}/revisiones",
        json=revision,
        headers=con_token(usuario_id),
    )


def consultar(sql):
    with engine.connect() as conexion:
        return conexion.execute(text(sql)).all()


def test_la_regional_ve_en_la_bandeja_la_entrega_aplicada(client, entrega_aplicada):
    respuesta = bandeja(client)

    assert respuesta.status_code == 200
    assert respuesta.json() == [EN_LA_BANDEJA]


@pytest.mark.parametrize("usuario_id", [3, 1], ids=["otra_regional", "direccion"])
def test_los_que_no_son_el_superior_no_la_ven_en_la_bandeja(
    client, entrega_aplicada, usuario_id
):
    assert bandeja(client, usuario_id).json() == []


def test_una_entrega_sin_recibir_no_aparece_en_la_bandeja(client, entrega_aplicada):
    with engine.begin() as conexion:
        insertar_entrega(conexion, 2, "PENDIENTE", "PENDIENTE", 4, 5)

    assert [registro["registro_id"] for registro in bandeja(client).json()] == [1]


def test_al_revisarlo_queda_revisado_con_la_version_y_sale_de_la_bandeja(
    client, entrega_aplicada
):
    respuesta = revisar(client, REVISAR)

    assert respuesta.status_code == 201
    revision = respuesta.json()
    assert revision | {"fecha": None} == {
        "resultado": "REVISADO",
        "version_revisada": 0,
        "motivo_observacion": None,
        "usuario": "logistico.regional_norte",
        "fecha": None,
    }
    assert consultar("SELECT estado_revision FROM movimiento WHERE id = 1") == [
        ("REVISADO",)
    ]
    assert consultar("SELECT version_revisada, usuario_id FROM revision") == [(0, 2)]
    assert bandeja(client).json() == []
    acta = client.get("/api/movimientos/1", headers=con_token(2)).json()
    assert acta["revisiones"] == [revision]


def test_al_observarlo_con_un_motivo_queda_observado_y_sale_de_la_bandeja(
    client, entrega_aplicada
):
    respuesta = revisar(client, OBSERVAR)

    assert respuesta.status_code == 201
    assert respuesta.json()["motivo_observacion"] == OBSERVAR["motivo_observacion"]
    assert consultar("SELECT estado_revision FROM movimiento WHERE id = 1") == [
        ("OBSERVADO",)
    ]
    assert consultar("SELECT resultado, motivo_observacion FROM revision") == [
        ("OBSERVADO", OBSERVAR["motivo_observacion"])
    ]
    assert bandeja(client).json() == []


@pytest.mark.parametrize(
    "revision",
    [{"resultado": "OBSERVADO", "version": 0}, OBSERVAR | {"motivo_observacion": " "}],
    ids=["sin_motivo", "motivo_en_blanco"],
)
def test_una_observacion_sin_motivo_responde_422(client, entrega_aplicada, revision):
    respuesta = revisar(client, revision)

    assert respuesta.status_code == 422
    assert consultar("SELECT * FROM revision") == []


def test_la_revision_de_una_version_ya_rectificada_responde_409(
    client, entrega_aplicada
):
    assert bandeja(client).json()[0]["version"] == 0
    with engine.begin() as conexion:
        conexion.execute(
            text(
                "INSERT INTO rectificacion (movimiento_id, version, fecha_hecho, "
                "numero_acta, descripcion, motivo, usuario_id) "
                "VALUES (1, 1, CURDATE(), '0001/2026', :descripcion, "
                "'Faltaba un chaleco', 4)"
            ),
            {"descripcion": DESCRIPCION},
        )

    respuesta = revisar(client, REVISAR)

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "detail": "La revision no corresponde a la version vigente"
    }
    assert consultar("SELECT estado_revision FROM movimiento WHERE id = 1") == [
        ("PENDIENTE",)
    ]
    assert consultar("SELECT * FROM revision") == []


@pytest.mark.parametrize(
    "usuario_id", [3, 1, 4], ids=["otra_regional", "direccion", "autor"]
)
def test_solo_el_superior_inmediato_revisa_el_movimiento(
    client, entrega_aplicada, usuario_id
):
    respuesta = revisar(client, REVISAR, usuario_id=usuario_id)

    assert respuesta.status_code == 403
    assert respuesta.json() == {
        "detail": "Solo el superior inmediato de la unidad revisa el movimiento"
    }


def test_lo_que_registra_direccion_no_se_revisa(client, entrega_aplicada):
    with engine.begin() as conexion:
        insertar_entrega(conexion, 2, "APLICADO", "NO_APLICA", 1, 2)

    assert revisar(client, REVISAR, movimiento_id=2).status_code == 403


@pytest.mark.parametrize("primera", [REVISAR, OBSERVAR], ids=["revisado", "observado"])
def test_un_movimiento_ya_revisado_u_observado_responde_409(
    client, entrega_aplicada, primera
):
    revisar(client, primera)

    respuesta = revisar(client, REVISAR)

    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": "El movimiento no está pendiente de revisión"}
    assert len(consultar("SELECT * FROM revision")) == 1


def test_una_entrega_sin_recibir_no_se_revisa(client, entrega_aplicada):
    with engine.begin() as conexion:
        insertar_entrega(conexion, 2, "PENDIENTE", "PENDIENTE", 4, 5)

    assert revisar(client, REVISAR, movimiento_id=2).status_code == 409


def test_un_movimiento_inexistente_responde_404(client, entrega_aplicada):
    assert revisar(client, REVISAR, movimiento_id=99).status_code == 404


def test_una_revision_espera_a_otra_en_curso_y_responde_409(client, entrega_aplicada):
    # Sin el FOR UPDATE la API lee el movimiento pendiente y termina guardando
    # una segunda revisión.
    resultado = {}
    with Session(engine) as otra:
        otra.exec(text("SELECT id FROM movimiento WHERE id = 1 FOR UPDATE"))
        otra.exec(
            text(
                "INSERT INTO revision (movimiento_id, resultado, version_revisada, "
                "usuario_id) VALUES (1, 'REVISADO', 0, 2)"
            )
        )
        otra.exec(
            text("UPDATE movimiento SET estado_revision = 'REVISADO' WHERE id = 1")
        )
        # Abre la conexión que va a usar la API, así la espera es solo el bloqueo.
        bandeja(client)

        hilo = threading.Thread(
            target=lambda: resultado.update(respuesta=revisar(client, REVISAR))
        )
        hilo.start()
        hilo.join(timeout=2)
        assert hilo.is_alive()
        otra.commit()
    hilo.join(timeout=10)

    assert resultado["respuesta"].status_code == 409
    assert resultado["respuesta"].json() == {
        "detail": "El movimiento no está pendiente de revisión"
    }
    assert len(consultar("SELECT * FROM revision")) == 1
