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
    (1, "logistico.direccion", 1),
    (2, "logistico.regional_norte", 2),
    (3, "logistico.regional_sur", 3),
    (4, "aux.unidad_a", 4),
    (5, "aux.unidad_b", 5),
    (6, "aux.unidad_c", 6),
]


@pytest.fixture
def alcance():
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
            text("INSERT INTO ubicacion (id, unidad_id, nombre) VALUES (1, 4, 'Sala')")
        )


def ejecutar(sql, **parametros):
    with engine.begin() as conexion:
        conexion.execute(text(sql), parametros)


def acta(id, estado, origen, destino, revision="NO_APLICA", dias=0):
    ejecutar(
        "INSERT INTO movimiento (id, tipo, estado, estado_revision, numero_acta, "
        "fecha_hecho, usuario_id, unidad_registrante_id, unidad_origen_id, "
        "unidad_destino_id, motivo, fecha_carga) "
        "VALUES (:id, 'ENTREGA', :estado, :revision, :numero, "
        "DATE(NOW() - INTERVAL :dias DAY), :origen, "
        ":origen, :origen, :destino, :motivo, NOW() - INTERVAL :dias DAY)",
        id=id,
        estado=estado,
        revision=revision,
        numero=f"{id:04d}/2026",
        origen=origen,
        destino=destino,
        motivo="Desistida" if estado == "RECHAZADO" else None,
        dias=dias,
    )


def observar(id, dias=0):
    ejecutar(
        "INSERT INTO revision (movimiento_id, resultado, motivo_observacion, "
        "version_revisada, usuario_id, fecha) "
        "VALUES (:id, 'OBSERVADO', 'No coincide', 0, 2, NOW() - INTERVAL :dias DAY)",
        id=id,
        dias=dias,
    )
    ejecutar(
        "UPDATE movimiento SET estado_revision = 'OBSERVADO' WHERE id = :id", id=id
    )


def devolver(id, usuario_id, dias=0):
    ejecutar(
        "INSERT INTO recepcion (movimiento_id, resultado, motivo, usuario_id, fecha) "
        "VALUES (:id, 'DEVUELTO', 'Falta un arma', :usuario_id, "
        "NOW() - INTERVAL :dias DAY)",
        id=id,
        usuario_id=usuario_id,
        dias=dias,
    )


def recibir(id, dias=0):
    ejecutar(
        "INSERT INTO recepcion (movimiento_id, resultado, usuario_id, fecha) "
        "VALUES (:id, 'ACEPTADO', 5, NOW() - INTERVAL :dias DAY)",
        id=id,
        dias=dias,
    )


def corregir(id, dias=0):
    ejecutar(
        "INSERT INTO rectificacion (movimiento_id, version, fecha_hecho, numero_acta, "
        "motivo, usuario_id, fecha) "
        "VALUES (:id, 1, DATE(NOW() - INTERVAL :dias DAY), :numero, "
        "'Corrige la serie', 4, NOW() - INTERVAL :dias DAY)",
        id=id,
        numero=f"{id:04d}/2026",
        dias=dias,
    )


def situacion(client, usuario_id, regional_id=None):
    parametros = {} if regional_id is None else {"regional_id": regional_id}
    return client.get(
        "/api/situacion",
        params=parametros,
        headers={"Authorization": f"Bearer {crear_token(usuario_id)}"},
    )


def grupo(cuerpo, etapa):
    return next(g for g in cuerpo["grupos"] if g["etapa"] == etapa)


def abiertas(cuerpo):
    return {u["id"]: u["abiertas"] for u in cuerpo["unidades"]}


def test_una_operacional_recibe_403(client, alcance):
    assert situacion(client, 4).status_code == 403


def test_la_regional_ve_su_regional_y_sus_unidades(client, alcance):
    cuerpo = situacion(client, 2).json()

    assert [u["id"] for u in cuerpo["unidades"]] == [2, 4, 5]


def test_direccion_ve_toda_la_jurisdiccion(client, alcance):
    cuerpo = situacion(client, 1).json()

    assert [u["id"] for u in cuerpo["unidades"]] == [1, 2, 4, 5, 3, 6]


def test_direccion_elige_una_regional(client, alcance):
    cuerpo = situacion(client, 1, regional_id=3).json()

    assert [u["id"] for u in cuerpo["unidades"]] == [3, 6]


def test_regional_id_que_no_es_una_regional_responde_422(client, alcance):
    assert situacion(client, 1, regional_id=4).status_code == 422
    assert situacion(client, 1, regional_id=1).status_code == 422


def test_una_regional_no_puede_elegir_regional(client, alcance):
    assert situacion(client, 2, regional_id=3).status_code == 422


def test_cuenta_bienes_y_fuera_de_servicio_por_tipo(client, alcance):
    ejecutar(
        "INSERT INTO bien (id, tipo_bien, marca, modelo, numero_serie, unidad_id, "
        "ubicacion_id, estado_operativo, de_baja) VALUES "
        "(1, 'ARMAMENTO', 'Bersa', 'TPR9', 'BT-1', 4, 1, 'EN_SERVICIO', FALSE), "
        "(2, 'ARMAMENTO', 'Bersa', 'TPR9', 'BT-2', 4, 1, 'FUERA_DE_SERVICIO', FALSE), "
        "(3, 'ARMAMENTO', 'Bersa', 'TPR9', 'BT-3', 4, NULL, 'EN_SERVICIO', TRUE)"
    )

    fila = next(u for u in situacion(client, 2).json()["unidades"] if u["id"] == 4)
    tipos = {t["tipo_bien"]: t for t in fila["tipos"]}

    assert [t["tipo_bien"] for t in fila["tipos"]] == [
        "ARMAMENTO",
        "CHALECO",
        "MOVIL",
        "EQUIPO_COMUNICACIONES",
    ]
    assert tipos["ARMAMENTO"]["total"] == 2
    assert tipos["ARMAMENTO"]["fuera_de_servicio"] == 1
    assert tipos["MOVIL"] == {"tipo_bien": "MOVIL", "total": 0, "fuera_de_servicio": 0}


def test_cada_acta_abierta_cuenta_en_su_grupo_y_su_unidad(client, alcance):
    acta(1, "PENDIENTE", 4, 5)
    acta(2, "APLICADO", 4, 5, revision="PENDIENTE")
    acta(3, "APLICADO", 4, 5, revision="PENDIENTE")
    observar(3)
    acta(4, "DEVUELTO", 4, 5)
    devolver(4, 5)

    cuerpo = situacion(client, 2).json()

    assert abiertas(cuerpo) == {2: 1, 4: 2, 5: 1}
    assert [(g["etapa"], g["cantidad"]) for g in cuerpo["grupos"]] == [
        ("POR_RECIBIR", 1),
        ("EN_REVISION", 1),
        ("OBSERVADA", 1),
        ("DEVUELTA", 1),
    ]


def test_los_dias_se_cuentan_desde_que_entro_al_estado(client, alcance):
    acta(1, "PENDIENTE", 4, 5, dias=5)
    acta(2, "APLICADO", 4, 5, revision="PENDIENTE", dias=10)
    observar(2, dias=2)

    cuerpo = situacion(client, 2).json()

    assert grupo(cuerpo, "POR_RECIBIR")["dias_mas_antigua"] == 5
    assert grupo(cuerpo, "OBSERVADA")["dias_mas_antigua"] == 2
    assert grupo(cuerpo, "DEVUELTA") == {
        "etapa": "DEVUELTA",
        "cantidad": 0,
        "dias_mas_antigua": None,
    }


def test_en_revision_y_devuelta_cuentan_desde_el_ultimo_paso(client, alcance):
    acta(1, "APLICADO", 4, 5, revision="PENDIENTE", dias=10)
    recibir(1, dias=4)
    acta(2, "APLICADO", 4, 5, revision="PENDIENTE", dias=9)
    recibir(2, dias=7)
    corregir(2, dias=3)
    acta(3, "DEVUELTO", 4, 5, dias=8)
    devolver(3, 5, dias=2)

    cuerpo = situacion(client, 2).json()

    assert [
        (d["movimiento_id"], d["etapa"], d["dias"]) for d in cuerpo["demoradas"]
    ] == [
        (1, "EN_REVISION", 4),
        (2, "EN_REVISION", 3),
        (3, "DEVUELTA", 2),
    ]
    assert grupo(cuerpo, "EN_REVISION")["dias_mas_antigua"] == 4
    assert grupo(cuerpo, "DEVUELTA")["dias_mas_antigua"] == 2


def test_las_actas_cerradas_no_cuentan(client, alcance):
    acta(1, "RECHAZADO", 4, 5)
    acta(2, "APLICADO", 4, 5, revision="REVISADO")

    cuerpo = situacion(client, 2).json()

    assert sum(g["cantidad"] for g in cuerpo["grupos"]) == 0
    assert cuerpo["demoradas"] == []


def test_fuera_del_alcance_no_cuenta(client, alcance):
    acta(1, "PENDIENTE", 6, 4)
    acta(2, "PENDIENTE", 4, 6)

    cuerpo = situacion(client, 2).json()

    assert abiertas(cuerpo)[4] == 1
    assert [d["movimiento_id"] for d in cuerpo["demoradas"]] == [1]


def test_las_mas_demoradas_son_cinco_y_van_ordenadas(client, alcance):
    for dias in range(1, 7):
        acta(dias, "PENDIENTE", 4, 5, dias=dias)

    demoradas = situacion(client, 2).json()["demoradas"]

    assert [d["dias"] for d in demoradas] == [6, 5, 4, 3, 2]
    assert demoradas[0] == {
        "movimiento_id": 6,
        "numero_acta": "0006/2026",
        "etapa": "POR_RECIBIR",
        "unidad_id": 5,
        "unidad": "Unidad Operacional B",
        "dias": 6,
    }
