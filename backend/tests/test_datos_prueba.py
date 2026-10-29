import bcrypt
import pytest
from cargar_datos_prueba import Carga, main
from sqlmodel import text

from app.core.database import engine

CONTRASENA = "demo"


@pytest.fixture
def datos_de_prueba():
    with engine.begin() as conexion:
        conexion.execute(text("DELETE FROM tipo_bien"))
        Carga(conexion).cargar(CONTRASENA)


def consultar(sql, **parametros):
    with engine.connect() as conexion:
        return [tuple(fila) for fila in conexion.execute(text(sql), parametros)]


def test_carga_las_unidades_con_un_usuario_cada_una(datos_de_prueba):
    assert consultar(
        "SELECT id, nombre, nivel, unidad_superior_id FROM unidad ORDER BY id"
    ) == [
        (1, "Dirección Logística", "DIRECCION", None),
        (2, "Unidad Regional Norte", "REGIONAL", 1),
        (3, "Unidad Regional Sur", "REGIONAL", 1),
        (4, "Unidad Operacional A", "OPERACIONAL", 2),
        (5, "Unidad Operacional B", "OPERACIONAL", 2),
        (6, "Unidad Operacional C", "OPERACIONAL", 3),
    ]
    usuarios = consultar(
        "SELECT unidad_id, hash_contrasena FROM usuario ORDER BY unidad_id"
    )
    assert [unidad_id for unidad_id, _ in usuarios] == [1, 2, 3, 4, 5, 6]
    assert all(
        bcrypt.checkpw(CONTRASENA.encode(), hash_contrasena.encode())
        for _, hash_contrasena in usuarios
    )


def test_el_bien_de_baja_no_aparece_en_el_inventario(datos_de_prueba):
    bajas = consultar("SELECT id, unidad_id FROM bien WHERE de_baja")
    assert [unidad_id for _, unidad_id in bajas] == [4]
    assert consultar(
        "SELECT COUNT(*) FROM v_inventario_unidad WHERE bien_id = :bien_id",
        bien_id=bajas[0][0],
    ) == [(0,)]


def test_la_entrega_de_a_a_b_aparece_pendiente_en_el_inventario_de_a(
    datos_de_prueba,
):
    assert consultar(
        "SELECT unidad_id, tipo_bien FROM v_inventario_unidad "
        "WHERE con_movimiento_pendiente"
    ) == [(4, "ARMAMENTO"), (4, "ARMAMENTO")]


def test_no_carga_nada_si_la_base_ya_tiene_datos(datos_de_prueba, monkeypatch, capsys):
    bienes = consultar("SELECT COUNT(*) FROM bien")
    monkeypatch.setenv("CONTRASENA_DEMO", CONTRASENA)
    main()
    assert "no se cargó nada" in capsys.readouterr().out
    assert consultar("SELECT COUNT(*) FROM bien") == bienes


def test_los_movimientos_aplicados_de_los_datos_de_prueba_tienen_numero_de_orden(
    datos_de_prueba,
):
    renglones = (
        "SELECT mb.orden, b.ultimo_orden FROM movimiento_bien mb "
        "JOIN movimiento m ON m.id = mb.movimiento_id "
        "JOIN bien b ON b.id = mb.bien_id WHERE m.tipo = :tipo"
    )
    assert consultar(renglones, tipo="BAJA") == [(1, 1)]
    assert consultar(renglones, tipo="ENTREGA") == [(None, 0), (None, 0)]
