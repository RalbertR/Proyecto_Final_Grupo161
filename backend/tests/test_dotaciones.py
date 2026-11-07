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

# id, tipo, serie, unidad, oficial, ubicación, de_baja, estado operativo
BIENES = [
    (1, "ARMAMENTO", "BT-1", 4, None, 1, False, "EN_SERVICIO"),
    (2, "CHALECO", "FM-1", 4, None, 1, False, "EN_SERVICIO"),
    (3, "ARMAMENTO", "BT-2", 4, 2, None, False, "EN_SERVICIO"),
    (4, "MOVIL", None, 4, None, 2, False, "EN_SERVICIO"),
    (5, "ARMAMENTO", "BT-3", 4, None, 1, False, "FUERA_DE_SERVICIO"),
    (6, "ARMAMENTO", "BT-4", 4, None, 1, False, "EN_SERVICIO"),
    (7, "ARMAMENTO", "GL-1", 1, None, 3, False, "EN_SERVICIO"),
    (8, "ARMAMENTO", "BT-5", 5, None, 4, False, "EN_SERVICIO"),
]

HOY = date.today().isoformat()

DOTACION = {
    "oficial_id": 1,
    "numero_acta": "0017/2026",
    "fecha_hecho": HOY,
    "descripcion": "Dotación de pistola y chaleco",
    "bienes": [1, 2],
}

GOMEZ = {"id": 1, "legajo": "50123", "nombre": "Gómez, Laura"}


@pytest.fixture
def unidad_con_oficiales():
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
                "unidad_id, oficial_id, ubicacion_id, de_baja, estado_operativo) "
                "VALUES (:id, :tipo, 'Marca', 'Modelo', :serie, :unidad, "
                ":oficial, :ubicacion, :de_baja, :estado)"
            ),
            [
                {
                    "id": id,
                    "tipo": tipo,
                    "serie": serie,
                    "unidad": unidad,
                    "oficial": oficial,
                    "ubicacion": ubicacion,
                    "de_baja": de_baja,
                    "estado": estado,
                }
                for id, tipo, serie, unidad, oficial, ubicacion, de_baja, estado in BIENES
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


def dotar(client, usuario_id=4, **cambios):
    return client.post(
        "/api/movimientos/dotaciones",
        json=DOTACION | cambios,
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


def pendiente_con_el_bien(bien_id, estado="PENDIENTE"):
    with engine.begin() as conexion:
        conexion.execute(
            text(
                "INSERT INTO movimiento (id, tipo, estado, estado_revision, "
                "numero_acta, fecha_hecho, usuario_id, unidad_registrante_id, "
                "unidad_origen_id, unidad_destino_id) VALUES (50, 'ENTREGA', "
                ":estado, 'PENDIENTE', '0015/2026', CURDATE(), 4, 4, 4, 5)"
            ),
            {"estado": estado},
        )
        conexion.execute(
            text(
                "INSERT INTO movimiento_bien (movimiento_id, bien_id, "
                "ubicacion_origen_id) VALUES (50, :bien_id, 1)"
            ),
            {"bien_id": bien_id},
        )


def test_registra_la_dotacion_aplicada_y_los_bienes_pasan_al_oficial(
    client, unidad_con_oficiales
):
    respuesta = dotar(client)

    assert respuesta.status_code == 201
    acta = respuesta.json()
    assert acta["tipo"] == "ENTREGA"
    assert acta["estado"] == "APLICADO"
    assert acta["numero_acta"] == "0017/2026"
    assert acta["fecha_hecho"] == HOY
    assert acta["unidad_origen"]["id"] == 4
    assert acta["unidad_destino"]["id"] == 4
    assert acta["oficial_origen"] is None
    assert acta["oficial_destino"] == GOMEZ
    assert [renglon["bien_id"] for renglon in acta["bienes"]] == [1, 2]
    for bien_id in (1, 2):
        assert tenencia(bien_id) == {
            "unidad_id": 4,
            "oficial_id": 1,
            "ubicacion_id": None,
        }


def test_cada_bien_toma_un_orden_nuevo_y_el_acta_queda_para_la_revision_de_la_regional(
    client, unidad_con_oficiales
):
    acta_id = dotar(client).json()["id"]

    for bien_id in (1, 2):
        historial = client.get(
            f"/api/bienes/{bien_id}/historial", headers=con_token(4)
        ).json()
        [evento] = historial["eventos"]
        assert (evento["registro_id"], evento["orden"]) == (acta_id, 1)
        assert evento["estado"] == "APLICADO"
        assert evento["estado_revision"] == "PENDIENTE"
        assert historial["bien"]["oficial_legajo"] == "50123"

    bandeja = client.get("/api/revisiones/bandeja", headers=con_token(2)).json()
    assert [fila["registro_id"] for fila in bandeja] == [acta_id]


def test_la_dotacion_de_direccion_no_queda_para_revision(client, unidad_con_oficiales):
    respuesta = dotar(client, 1, oficial_id=5, bienes=[7])

    assert respuesta.status_code == 201
    assert respuesta.json()["estado_revision"] == "NO_APLICA"
    assert tenencia(7)["oficial_id"] == 5


def test_el_detalle_del_acta_trae_el_oficial_destino(client, unidad_con_oficiales):
    acta_id = dotar(client).json()["id"]

    respuesta = client.get(f"/api/movimientos/{acta_id}", headers=con_token(4))

    assert respuesta.status_code == 200
    assert respuesta.json()["oficial_destino"] == GOMEZ


def test_un_bien_fuera_de_servicio_responde_409(client, unidad_con_oficiales):
    respuesta = dotar(client, bienes=[1, 5])

    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": "Uno de los bienes está fuera de servicio"}
    assert cantidad_de_actas() == 0
    assert tenencia(1)["oficial_id"] is None


def test_un_bien_ya_asignado_a_un_oficial_responde_409(client, unidad_con_oficiales):
    respuesta = dotar(client, bienes=[1, 3])

    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": "Uno de los bienes no está en depósito"}
    assert cantidad_de_actas() == 0


@pytest.mark.parametrize("estado", ["PENDIENTE", "DEVUELTO"])
def test_un_bien_con_un_movimiento_pendiente_responde_409(
    client, unidad_con_oficiales, estado
):
    pendiente_con_el_bien(6, estado)

    respuesta = dotar(client, bienes=[1, 6])

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "detail": "Uno de los bienes ya tiene un movimiento pendiente"
    }
    assert cantidad_de_actas() == 1


def test_un_oficial_con_un_traslado_pendiente_responde_409(
    client, unidad_con_oficiales
):
    with engine.begin() as conexion:
        conexion.execute(
            text(
                "INSERT INTO traslado_oficial (oficial_id, unidad_origen_id, "
                "unidad_destino_id, usuario_solicitante_id) VALUES (2, 4, 5, 4)"
            )
        )

    respuesta = dotar(client, oficial_id=2)

    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": "El oficial tiene un traslado pendiente"}
    assert cantidad_de_actas() == 0


@pytest.mark.parametrize(
    "oficial_id", [4, 3, 99], ids=["de_otra_unidad", "inactivo", "inexistente"]
)
def test_un_oficial_de_otra_unidad_o_inactivo_responde_422(
    client, unidad_con_oficiales, oficial_id
):
    respuesta = dotar(client, oficial_id=oficial_id)

    assert respuesta.status_code == 422
    assert respuesta.json() == {
        "detail": "El oficial tiene que ser activo y de su unidad"
    }
    assert cantidad_de_actas() == 0


@pytest.mark.parametrize(
    "cambios",
    [
        {"bienes": [1, 4]},
        {"numero_acta": "17/2026"},
        {"fecha_hecho": (date.today() + timedelta(days=1)).isoformat()},
        {"bienes": []},
    ],
    ids=["dos_areas", "acta_sin_formato", "fecha_posterior_a_hoy", "sin_bienes"],
)
def test_una_dotacion_con_datos_invalidos_responde_422(
    client, unidad_con_oficiales, cambios
):
    respuesta = dotar(client, **cambios)

    assert respuesta.status_code == 422
    assert cantidad_de_actas() == 0


@pytest.mark.parametrize("bien_id", [8, 99], ids=["de_otra_unidad", "inexistente"])
def test_un_bien_que_no_es_de_la_unidad_responde_403(
    client, unidad_con_oficiales, bien_id
):
    respuesta = dotar(client, bienes=[1, bien_id])

    assert respuesta.status_code == 403
    assert respuesta.json() == {"detail": "Uno de los bienes no pertenece a su unidad"}


def test_lista_los_oficiales_activos_de_la_unidad(client, unidad_con_oficiales):
    respuesta = client.get("/api/oficiales", headers=con_token(4))

    assert respuesta.status_code == 200
    assert respuesta.json() == [
        {"id": 2, "legajo": "50124", "nombre": "Acosta, Pedro"},
        GOMEZ,
    ]


def test_los_oficiales_se_piden_con_sesion(client, unidad_con_oficiales):
    assert client.get("/api/oficiales").status_code == 401
