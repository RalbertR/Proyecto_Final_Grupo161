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
    (4, "aux.unidad_a", 4),
    (5, "aux.unidad_b", 5),
    (6, "aux.unidad_c", 6),
]

BIENES = [
    (1, "ARMAMENTO", "Bersa", "TPR9", "BT-1", "EN_SERVICIO", 4, None, 1, False),
    (2, "CHALECO", "FM S.A.", "RB3", "FM-1", "FUERA_DE_SERVICIO", 4, 1, None, False),
    (3, "ARMAMENTO", "Glock", "17", "GL-1", "EN_SERVICIO", 4, None, None, True),
    (4, "ARMAMENTO", "Bersa", "TPR9", "BT-2", "EN_SERVICIO", 4, None, 1, False),
    (5, "ARMAMENTO", "Bersa", "TPR9", "BT-3", "EN_SERVICIO", 5, None, 2, False),
]

EN_DEPOSITO = {
    "unidad_id": 4,
    "unidad": "Unidad Operacional A",
    "bien_id": 1,
    "tipo_bien": "ARMAMENTO",
    "identificacion": "BT-1",
    "marca": "Bersa",
    "modelo": "TPR9",
    "estado_operativo": "EN_SERVICIO",
    "tenencia": "DEPOSITO",
    "ubicacion": "Sala de Armas",
    "oficial_legajo": None,
    "oficial": None,
    "con_movimiento_pendiente": False,
}

CON_PENDIENTE = EN_DEPOSITO | {
    "bien_id": 4,
    "identificacion": "BT-2",
    "con_movimiento_pendiente": True,
}

EN_DOTACION = EN_DEPOSITO | {
    "bien_id": 2,
    "tipo_bien": "CHALECO",
    "identificacion": "FM-1",
    "marca": "FM S.A.",
    "modelo": "RB3",
    "estado_operativo": "FUERA_DE_SERVICIO",
    "tenencia": "DOTACION",
    "ubicacion": None,
    "oficial_legajo": "10001",
    "oficial": "Gómez, Laura",
}


@pytest.fixture
def inventario():
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
                "INSERT INTO ubicacion (id, unidad_id, nombre) "
                "VALUES (1, 4, 'Sala de Armas'), (2, 5, 'Sala de Armas')"
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
                "estado_operativo, unidad_id, oficial_id, ubicacion_id, de_baja) "
                "VALUES (:id, :tipo_bien, :marca, :modelo, :serie, :estado, "
                ":unidad_id, :oficial_id, :ubicacion_id, :de_baja)"
            ),
            [
                {
                    "id": id,
                    "tipo_bien": tipo_bien,
                    "marca": marca,
                    "modelo": modelo,
                    "serie": serie,
                    "estado": estado,
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
                    estado,
                    unidad_id,
                    oficial_id,
                    ubicacion_id,
                    de_baja,
                ) in BIENES
            ],
        )
        conexion.execute(
            text(
                "INSERT INTO movimiento (id, tipo, estado, estado_revision, numero_acta, "
                "fecha_hecho, usuario_id, unidad_registrante_id, unidad_origen_id, "
                "unidad_destino_id) VALUES (1, 'ENTREGA', 'PENDIENTE', 'PENDIENTE', "
                "'0015/2026', CURDATE(), 4, 4, 4, 5)"
            )
        )
        conexion.execute(
            text(
                "INSERT INTO movimiento_bien (movimiento_id, bien_id, ubicacion_origen_id) "
                "VALUES (1, 4, 1)"
            )
        )


def con_token(usuario_id):
    return {"Authorization": f"Bearer {crear_token(usuario_id)}"}


def pedir_inventario(client, usuario_id, **filtros):
    return client.get("/api/inventario", params=filtros, headers=con_token(usuario_id))


def test_operacional_ve_solo_los_bienes_de_su_unidad_con_su_tenencia(
    client, inventario
):
    respuesta = pedir_inventario(client, 4)

    assert respuesta.status_code == 200
    assert respuesta.json() == [EN_DEPOSITO, CON_PENDIENTE, EN_DOTACION]


def test_el_bien_de_baja_no_aparece(client, inventario):
    bienes = [fila["bien_id"] for fila in pedir_inventario(client, 4).json()]

    assert 3 not in bienes


def test_el_bien_con_un_movimiento_pendiente_aparece_marcado(client, inventario):
    pendientes = [
        fila["bien_id"]
        for fila in pedir_inventario(client, 4).json()
        if fila["con_movimiento_pendiente"]
    ]

    assert pendientes == [4]


def test_filtra_por_tipo_de_bien(client, inventario):
    respuesta = pedir_inventario(client, 4, tipo_bien="CHALECO")

    assert respuesta.json() == [EN_DOTACION]


def test_una_unidad_sin_bienes_devuelve_la_lista_vacia(client, inventario):
    respuesta = pedir_inventario(client, 6)

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_pedir_la_propia_unidad_devuelve_su_inventario(client, inventario):
    respuesta = pedir_inventario(client, 5, unidad_id=5)

    assert [fila["bien_id"] for fila in respuesta.json()] == [5]


def test_pedir_el_inventario_de_otra_unidad_responde_403(client, inventario):
    respuesta = pedir_inventario(client, 4, unidad_id=5)

    assert respuesta.status_code == 403
    assert respuesta.json() == {"detail": "No tiene acceso al inventario de esa unidad"}
