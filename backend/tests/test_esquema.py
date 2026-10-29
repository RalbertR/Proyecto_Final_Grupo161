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
