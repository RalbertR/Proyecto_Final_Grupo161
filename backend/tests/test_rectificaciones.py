from datetime import date, timedelta

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
    (1, "logistico.direccion", 1),
    (2, "logistico.regional_norte", 2),
    (4, "aux.unidad_a", 4),
    (5, "aux.unidad_b", 5),
]

INSERTAR_ENTREGA = (
    "INSERT INTO movimiento (id, tipo, estado, estado_revision, numero_acta, "
    "fecha_hecho, descripcion, usuario_id, unidad_registrante_id, "
    "unidad_origen_id, unidad_destino_id) "
    "VALUES (:id, 'ENTREGA', 'APLICADO', :estado_revision, '0016/2026', "
    ":fecha_hecho, :descripcion, :origen, :origen, :origen, :destino)"
)

# Días antes de hoy, para no depender de la zona horaria de la base.
FECHA_ORIGINAL = date.today() - timedelta(days=2)
FECHA_CORREGIDA = date.today() - timedelta(days=3)

DESCRIPCION = "Refuerzo de armamento para la Unidad Operacional B"

MOTIVO_OBSERVACION = "La fecha no coincide con el acta firmada"

RECTIFICACION = {
    "fecha_hecho": FECHA_CORREGIDA.isoformat(),
    "numero_acta": "0016/2026",
    "descripcion": DESCRIPCION,
    "motivo": "Se corrige la fecha según el acta firmada",
}


@pytest.fixture
def entrega_observada():
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
        insertar_entrega(conexion, 1, "OBSERVADO", 4, 5)
        conexion.execute(
            text(
                "INSERT INTO revision (movimiento_id, resultado, motivo_observacion, "
                "version_revisada, usuario_id) VALUES (1, 'OBSERVADO', :motivo, 0, 2)"
            ),
            {"motivo": MOTIVO_OBSERVACION},
        )


def insertar_entrega(conexion, id, estado_revision, origen, destino):
    conexion.execute(
        text(INSERTAR_ENTREGA),
        {
            "id": id,
            "estado_revision": estado_revision,
            "fecha_hecho": FECHA_ORIGINAL,
            "descripcion": DESCRIPCION,
            "origen": origen,
            "destino": destino,
        },
    )


def con_token(usuario_id):
    return {"Authorization": f"Bearer {crear_token(usuario_id)}"}


def observados(client, usuario_id=4):
    return client.get("/api/movimientos/observados", headers=con_token(usuario_id))


def rectificar(client, rectificacion=RECTIFICACION, movimiento_id=1, usuario_id=4):
    return client.post(
        f"/api/movimientos/{movimiento_id}/rectificaciones",
        json=rectificacion,
        headers=con_token(usuario_id),
    )


def consultar(sql):
    with engine.connect() as conexion:
        return conexion.execute(text(sql)).all()


def test_la_unidad_recibe_sus_movimientos_observados_con_el_motivo(
    client, entrega_observada
):
    respuesta = observados(client)

    assert respuesta.status_code == 200
    assert [movimiento["id"] for movimiento in respuesta.json()] == [1]
    assert respuesta.json()[0]["revisiones"][0]["motivo_observacion"] == (
        MOTIVO_OBSERVACION
    )


@pytest.mark.parametrize("usuario_id", [5, 2], ids=["destino", "regional"])
def test_las_demas_unidades_no_reciben_el_observado(
    client, entrega_observada, usuario_id
):
    assert observados(client, usuario_id).json() == []


def test_la_correccion_queda_como_version_1_sin_modificar_el_original(
    client, entrega_observada
):
    respuesta = rectificar(client)

    assert respuesta.status_code == 201
    acta = respuesta.json()
    assert acta["version_vigente"] == 1
    assert acta["fecha_hecho"] == FECHA_CORREGIDA.isoformat()
    assert acta["estado_revision"] == "PENDIENTE"
    assert all(version.pop("fecha") for version in acta["versiones"])
    assert acta["versiones"] == [
        {
            "version": 0,
            "fecha_hecho": FECHA_ORIGINAL.isoformat(),
            "numero_acta": "0016/2026",
            "descripcion": DESCRIPCION,
            "motivo": None,
            "usuario": "aux.unidad_a",
        },
        {"version": 1, **RECTIFICACION, "usuario": "aux.unidad_a"},
    ]
    assert consultar(
        "SELECT fecha_hecho, numero_acta, descripcion, estado_revision FROM movimiento"
    ) == [(FECHA_ORIGINAL, "0016/2026", DESCRIPCION, "PENDIENTE")]
    bandeja = client.get("/api/revisiones/bandeja", headers=con_token(2)).json()
    assert [(registro["registro_id"], registro["version"]) for registro in bandeja] == [
        (1, 1)
    ]
    assert observados(client).json() == []


def test_una_segunda_correccion_queda_como_version_2(client, entrega_observada):
    rectificar(client)

    respuesta = rectificar(
        client,
        RECTIFICACION
        | {"numero_acta": "0017/2026", "motivo": "Se corrige el número de acta"},
    )

    assert respuesta.status_code == 201
    acta = respuesta.json()
    assert acta["version_vigente"] == 2
    assert acta["numero_acta"] == "0017/2026"
    assert [version["version"] for version in acta["versiones"]] == [0, 1, 2]
    assert consultar("SELECT version FROM rectificacion ORDER BY version") == [
        (1,),
        (2,),
    ]


@pytest.mark.parametrize(
    "usuario_id", [5, 2, 1], ids=["destino", "regional", "direccion"]
)
def test_otra_unidad_no_corrige_el_movimiento(client, entrega_observada, usuario_id):
    respuesta = rectificar(client, usuario_id=usuario_id)

    assert respuesta.status_code == 403
    assert respuesta.json() == {
        "detail": "Solo la unidad que registró el movimiento lo corrige"
    }
    assert consultar("SELECT * FROM rectificacion") == []


@pytest.mark.parametrize(
    "estado",
    [
        "estado = 'PENDIENTE'",
        "estado = 'RECHAZADO'",
        (
            "estado = 'ANULADO', anulado_por_id = 2, fecha_anulacion = NOW(), "
            "motivo_anulacion = 'Se cargó un bien equivocado'"
        ),
    ],
    ids=["pendiente_de_recepcion", "rechazado", "anulado"],
)
def test_solo_se_corrigen_movimientos_aplicados(client, entrega_observada, estado):
    with engine.begin() as conexion:
        conexion.execute(text(f"UPDATE movimiento SET {estado} WHERE id = 1"))

    respuesta = rectificar(client)

    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": "Solo se corrigen movimientos aplicados"}
    assert consultar("SELECT * FROM rectificacion") == []


@pytest.mark.parametrize(
    "cambios",
    [
        {"motivo": None},
        {"motivo": " "},
        {"numero_acta": "16/2026"},
        {"fecha_hecho": (date.today() + timedelta(days=1)).isoformat()},
    ],
    ids=["sin_motivo", "motivo_en_blanco", "acta_sin_formato", "fecha_futura"],
)
def test_una_correccion_invalida_responde_422(client, entrega_observada, cambios):
    respuesta = rectificar(client, RECTIFICACION | cambios)

    assert respuesta.status_code == 422
    assert consultar("SELECT * FROM rectificacion") == []


def test_el_detalle_muestra_que_version_se_observo_y_cual_se_aprobo(
    client, entrega_observada
):
    rectificar(client)
    client.post(
        "/api/movimientos/1/revisiones",
        json={"resultado": "REVISADO", "version": 1},
        headers=con_token(2),
    )

    respuesta = client.get("/api/movimientos/1", headers=con_token(4))

    assert respuesta.status_code == 200
    acta = respuesta.json()
    assert acta["estado_revision"] == "REVISADO"
    assert [version["version"] for version in acta["versiones"]] == [0, 1]
    assert [
        (revision["resultado"], revision["version_revisada"])
        for revision in acta["revisiones"]
    ] == [("OBSERVADO", 0), ("REVISADO", 1)]


def test_lo_que_corrige_direccion_no_vuelve_a_revision(client, entrega_observada):
    with engine.begin() as conexion:
        insertar_entrega(conexion, 2, "NO_APLICA", 1, 2)

    respuesta = rectificar(client, movimiento_id=2, usuario_id=1)

    assert respuesta.status_code == 201
    assert respuesta.json()["estado_revision"] == "NO_APLICA"


def test_un_movimiento_inexistente_responde_404(client, entrega_observada):
    assert rectificar(client, movimiento_id=99).status_code == 404
