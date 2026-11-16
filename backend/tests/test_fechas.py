from datetime import date

from app.core.fechas import hoy_en_argentina


def test_a_las_22_de_argentina_sigue_siendo_el_mismo_dia(a_las_22_de_argentina):
    assert hoy_en_argentina() == date(2026, 11, 10)
