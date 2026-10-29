import pytest
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlmodel import text


def insertar_unidad(session, id, nivel, superior):
    session.exec(
        text(
            "INSERT INTO unidad (id, nombre, nivel, unidad_superior_id) "
            "VALUES (:id, :nombre, :nivel, :superior)"
        ).bindparams(id=id, nombre=f"Unidad {id}", nivel=nivel, superior=superior)
    )


@pytest.fixture
def direccion_y_regional(session):
    insertar_unidad(session, 1, "DIRECCION", None)
    insertar_unidad(session, 2, "REGIONAL", 1)


def test_un_bien_activo_sin_oficial_ni_ubicacion_es_rechazado(session):
    session.exec(
        text(
            "INSERT INTO unidad (id, nombre, nivel) "
            "VALUES (1, 'Dirección Logística', 'DIRECCION')"
        )
    )

    with pytest.raises(OperationalError, match="Tenencia invalida"):
        session.exec(
            text(
                "INSERT INTO bien (tipo_bien, marca, modelo, numero_serie, unidad_id) "
                "VALUES ('ARMAMENTO', 'Bersa', 'TPR9', 'A0001', 1)"
            )
        )


def test_una_operacional_que_depende_de_una_regional_se_acepta(
    session, direccion_y_regional
):
    insertar_unidad(session, 3, "OPERACIONAL", 2)


def test_una_operacional_que_depende_de_otra_operacional_es_rechazada(
    session, direccion_y_regional
):
    insertar_unidad(session, 3, "OPERACIONAL", 2)

    with pytest.raises(IntegrityError):
        insertar_unidad(session, 4, "OPERACIONAL", 3)


def test_una_operacional_que_depende_de_direccion_es_rechazada(
    session, direccion_y_regional
):
    with pytest.raises(IntegrityError):
        insertar_unidad(session, 3, "OPERACIONAL", 1)


def test_una_regional_que_depende_de_otra_regional_es_rechazada(
    session, direccion_y_regional
):
    with pytest.raises(IntegrityError):
        insertar_unidad(session, 3, "REGIONAL", 2)


def test_cambiar_el_nivel_de_una_regional_con_operacionales_es_rechazado(
    session, direccion_y_regional
):
    insertar_unidad(session, 3, "OPERACIONAL", 2)

    with pytest.raises(IntegrityError):
        session.exec(text("UPDATE unidad SET nivel = 'OPERACIONAL' WHERE id = 2"))


@pytest.fixture
def organizacion(session, direccion_y_regional):
    insertar_unidad(session, 4, "OPERACIONAL", 2)
    insertar_unidad(session, 5, "OPERACIONAL", 2)
    session.exec(
        text(
            "INSERT INTO usuario (id, nombre_usuario, hash_contrasena, unidad_id) "
            "VALUES (1, 'aux.unidad_a', 'x', 4)"
        )
    )
    session.exec(
        text(
            "INSERT INTO ubicacion (id, unidad_id, nombre) "
            "VALUES (1, 4, 'Sala de Armas'), (2, 5, 'Sala de Armas')"
        )
    )
    session.exec(
        text(
            "INSERT INTO bien "
            "(id, tipo_bien, marca, modelo, numero_serie, unidad_id, ubicacion_id) "
            "VALUES (1, 'ARMAMENTO', 'Bersa', 'TPR9', 'BT-1', 4, 1), "
            "(2, 'ARMAMENTO', 'Bersa', 'TPR9', 'BT-2', 4, 1)"
        )
    )


def insertar_renglones(session, movimiento_id, bienes):
    for bien_id in bienes:
        session.exec(
            text(
                "INSERT INTO movimiento_bien "
                "(movimiento_id, bien_id, ubicacion_origen_id) VALUES (:m, :b, 1)"
            ).bindparams(m=movimiento_id, b=bien_id)
        )


def reubicar(session, movimiento_id, bienes):
    session.exec(
        text(
            "INSERT INTO movimiento (id, tipo, estado, estado_revision, fecha_hecho, "
            "usuario_id, unidad_registrante_id, unidad_origen_id, unidad_destino_id) "
            "VALUES (:id, 'REUBICACION', 'APLICADO', 'NO_APLICA', CURDATE(), "
            "1, 4, 4, 4)"
        ).bindparams(id=movimiento_id)
    )
    insertar_renglones(session, movimiento_id, bienes)


def entregar(session, movimiento_id, bienes, estado="PENDIENTE"):
    session.exec(
        text(
            "INSERT INTO movimiento (id, tipo, estado, estado_revision, numero_acta, "
            "fecha_hecho, usuario_id, unidad_registrante_id, unidad_origen_id, "
            "unidad_destino_id) VALUES (:id, 'ENTREGA', :estado, 'PENDIENTE', "
            "'0001/2026', CURDATE(), 1, 4, 4, 5)"
        ).bindparams(id=movimiento_id, estado=estado)
    )
    insertar_renglones(session, movimiento_id, bienes)


def pasar_a(session, movimiento_id, estado):
    session.exec(
        text("UPDATE movimiento SET estado = :estado WHERE id = :id").bindparams(
            estado=estado, id=movimiento_id
        )
    )


def registrar_cambio_de_estado(session, cambio_id, bien_id):
    session.exec(
        text(
            "INSERT INTO cambio_estado_operativo (id, bien_id, estado_anterior, "
            "estado_nuevo, observaciones, estado_revision, usuario_id, "
            "unidad_registrante_id) VALUES (:id, :bien_id, 'FUERA_DE_SERVICIO', "
            "'EN_SERVICIO', 'Reparada por el armero', 'PENDIENTE', 1, 4)"
        ).bindparams(id=cambio_id, bien_id=bien_id)
    )


def orden(session, bien_id):
    renglones = (
        session.exec(
            text(
                "SELECT orden FROM movimiento_bien WHERE bien_id = :b "
                "ORDER BY movimiento_id"
            ).bindparams(b=bien_id)
        )
        .scalars()
        .all()
    )
    ultimo = session.exec(
        text("SELECT ultimo_orden FROM bien WHERE id = :b").bindparams(b=bien_id)
    ).scalar_one()
    return renglones, ultimo


def test_un_movimiento_aplicado_le_da_al_bien_el_siguiente_numero_de_orden(
    session, organizacion
):
    reubicar(session, 1, [1])
    reubicar(session, 2, [1])

    assert orden(session, 1) == ([1, 2], 2)


def test_una_entrega_pendiente_toma_numero_recien_al_aplicarse(session, organizacion):
    entregar(session, 1, [1])
    assert orden(session, 1) == ([None], 0)

    pasar_a(session, 1, "APLICADO")

    assert orden(session, 1) == ([1], 1)


def test_cada_bien_de_un_acta_toma_su_propio_numero(session, organizacion):
    reubicar(session, 1, [1])
    entregar(session, 2, [1, 2])

    pasar_a(session, 2, "APLICADO")

    assert orden(session, 1) == ([1, 2], 2)
    assert orden(session, 2) == ([1], 1)


def test_una_entrega_rechazada_no_toma_numero(session, organizacion):
    entregar(session, 1, [1])

    pasar_a(session, 1, "RECHAZADO")

    assert orden(session, 1) == ([None], 0)


def test_anular_un_movimiento_aplicado_conserva_su_numero(session, organizacion):
    reubicar(session, 1, [1])

    session.exec(
        text(
            "UPDATE movimiento SET estado = 'ANULADO', anulado_por_id = 1, "
            "fecha_anulacion = NOW(), motivo_anulacion = 'Carga equivocada' "
            "WHERE id = 1"
        )
    )

    assert orden(session, 1) == ([1], 1)


def test_un_cambio_de_estado_toma_el_siguiente_numero_del_bien(session, organizacion):
    reubicar(session, 1, [1])

    registrar_cambio_de_estado(session, 1, 1)

    assert (
        session.exec(
            text("SELECT orden FROM cambio_estado_operativo WHERE id = 1")
        ).scalar_one()
        == 2
    )
    assert orden(session, 1) == ([1], 2)


def test_un_numero_de_orden_repetido_para_el_mismo_bien_es_rechazado(
    session, organizacion
):
    reubicar(session, 1, [1])
    reubicar(session, 2, [1])

    with pytest.raises(IntegrityError):
        session.exec(
            text("UPDATE movimiento_bien SET orden = 1 WHERE movimiento_id = 2")
        )
