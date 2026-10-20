import pytest
from sqlalchemy.exc import OperationalError
from sqlmodel import text


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
