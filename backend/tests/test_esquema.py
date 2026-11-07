import threading

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlmodel import Session, text

from app.core.database import engine

FILA_CON_DEPENDIENTES = 1451
PASAR_LA_REGIONAL_2_A_OPERACIONAL_DE_LA_3 = (
    "UPDATE unidad SET nivel = 'OPERACIONAL', unidad_superior_id = 3 WHERE id = 2"
)


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
    insertar_unidad(session, 3, "REGIONAL", 1)
    insertar_unidad(session, 4, "OPERACIONAL", 2)

    with pytest.raises(IntegrityError) as error:
        session.exec(text(PASAR_LA_REGIONAL_2_A_OPERACIONAL_DE_LA_3))
    assert error.value.orig.args[0] == FILA_CON_DEPENDIENTES


def test_cambiar_el_nivel_de_una_regional_sin_operacionales_se_acepta(
    session, direccion_y_regional
):
    insertar_unidad(session, 3, "REGIONAL", 1)

    session.exec(text(PASAR_LA_REGIONAL_2_A_OPERACIONAL_DE_LA_3))


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


def rectificar(session, movimiento_id, version):
    session.exec(
        text(
            "INSERT INTO rectificacion (movimiento_id, version, fecha_hecho, "
            "numero_acta, motivo, usuario_id) VALUES (:m, :v, CURDATE(), "
            "'0001/2026', 'Se corrige la fecha según el acta firmada', 1)"
        ).bindparams(m=movimiento_id, v=version)
    )


def revisar(session, version, movimiento_id=None, cambio_estado_id=None):
    session.exec(
        text(
            "INSERT INTO revision (movimiento_id, cambio_estado_id, resultado, "
            "version_revisada, usuario_id) VALUES (:m, :c, 'REVISADO', :v, 1)"
        ).bindparams(m=movimiento_id, c=cambio_estado_id, v=version)
    )


def test_una_revision_de_la_version_original_se_acepta(session, organizacion):
    entregar(session, 1, [1], estado="APLICADO")

    revisar(session, 0, movimiento_id=1)


def test_una_revision_de_una_version_anterior_a_la_vigente_es_rechazada(
    session, organizacion
):
    entregar(session, 1, [1], estado="APLICADO")
    rectificar(session, 1, 1)

    with pytest.raises(OperationalError, match="version vigente"):
        revisar(session, 0, movimiento_id=1)
    revisar(session, 1, movimiento_id=1)


def test_una_revision_de_una_version_que_no_existe_es_rechazada(session, organizacion):
    entregar(session, 1, [1], estado="APLICADO")

    with pytest.raises(OperationalError, match="version vigente"):
        revisar(session, 1, movimiento_id=1)


def rectificar_cambio_de_estado(session, cambio_estado_id, version, documento_id=None):
    session.exec(
        text(
            "INSERT INTO rectificacion_cambio_estado (cambio_estado_id, version, "
            "observaciones, documento_id, motivo, usuario_id) VALUES (:c, :v, "
            "'Reparada y probada en el polígono', :documento, "
            "'Se completa la observación', 1)"
        ).bindparams(c=cambio_estado_id, v=version, documento=documento_id)
    )


def test_la_revision_de_un_cambio_de_estado_controla_su_version(session, organizacion):
    registrar_cambio_de_estado(session, 1, 1)
    rectificar_cambio_de_estado(session, 1, 1)

    with pytest.raises(OperationalError, match="version vigente"):
        revisar(session, 0, cambio_estado_id=1)
    revisar(session, 1, cambio_estado_id=1)


def en_otra_transaccion(operacion):
    resultado = {}

    def ejecutar_y_confirmar():
        with Session(engine) as otra:
            try:
                operacion(otra)
                otra.commit()
            except OperationalError as error:
                resultado["error"] = str(error)

    hilo = threading.Thread(target=ejecutar_y_confirmar)
    hilo.start()
    return hilo, resultado


def test_una_revision_espera_la_rectificacion_en_curso_del_movimiento(
    session, organizacion
):
    entregar(session, 1, [1], estado="APLICADO")
    session.commit()

    with Session(engine) as autor:
        rectificar(autor, 1, 1)
        hilo, resultado = en_otra_transaccion(
            lambda revisor: revisar(revisor, 0, movimiento_id=1)
        )
        hilo.join(timeout=1)
        assert hilo.is_alive()
        autor.commit()
    hilo.join(timeout=10)

    assert "version vigente" in resultado["error"]


def test_una_revision_espera_la_rectificacion_en_curso_del_cambio_de_estado(
    session, organizacion
):
    registrar_cambio_de_estado(session, 1, 1)
    session.commit()

    with Session(engine) as autor:
        rectificar_cambio_de_estado(autor, 1, 1)
        hilo, resultado = en_otra_transaccion(
            lambda revisor: revisar(revisor, 0, cambio_estado_id=1)
        )
        hilo.join(timeout=1)
        assert hilo.is_alive()
        autor.commit()
    hilo.join(timeout=10)

    assert "version vigente" in resultado["error"]


def test_una_rectificacion_espera_la_revision_en_curso_del_movimiento(
    session, organizacion
):
    entregar(session, 1, [1], estado="APLICADO")
    session.commit()

    with Session(engine) as revisor:
        revisar(revisor, 0, movimiento_id=1)
        hilo, resultado = en_otra_transaccion(lambda autor: rectificar(autor, 1, 1))
        hilo.join(timeout=1)
        assert hilo.is_alive()
        revisor.commit()
    hilo.join(timeout=10)

    assert resultado == {}


def test_una_rectificacion_espera_la_revision_en_curso_del_cambio_de_estado(
    session, organizacion
):
    registrar_cambio_de_estado(session, 1, 1)
    session.commit()

    with Session(engine) as revisor:
        revisar(revisor, 0, cambio_estado_id=1)
        hilo, resultado = en_otra_transaccion(
            lambda autor: rectificar_cambio_de_estado(autor, 1, 1)
        )
        hilo.join(timeout=1)
        assert hilo.is_alive()
        revisor.commit()
    hilo.join(timeout=10)

    assert resultado == {}


def test_el_historial_muestra_el_numero_de_orden_de_cada_registro(
    session, organizacion
):
    reubicar(session, 1, [1])
    registrar_cambio_de_estado(session, 1, 1)

    historial = session.exec(
        text(
            "SELECT registro, orden, fecha_carga FROM v_historial_bien "
            "WHERE bien_id = 1 ORDER BY orden"
        )
    ).all()

    assert [(registro, orden) for registro, orden, _ in historial] == [
        ("MOVIMIENTO", 1),
        ("CAMBIO_ESTADO", 2),
    ]
    assert all(fecha_carga is not None for _, _, fecha_carga in historial)


def test_la_bandeja_muestra_la_version_vigente(session, organizacion):
    entregar(session, 1, [1], estado="APLICADO")
    version_en_la_bandeja = text(
        "SELECT version_vigente FROM v_bandeja_revision "
        "WHERE unidad_revisora_id = 2 AND registro = 'MOVIMIENTO' AND registro_id = 1"
    )
    assert session.exec(version_en_la_bandeja).scalar_one() == 0

    rectificar(session, 1, 1)

    assert session.exec(version_en_la_bandeja).scalar_one() == 1


def insertar_oficial(session, id, unidad_id):
    session.exec(
        text(
            "INSERT INTO oficial (id, legajo, apellido, nombre, unidad_id) "
            "VALUES (:id, :legajo, 'Gómez', 'Laura', :unidad_id)"
        ).bindparams(id=id, legajo=f"5012{id}", unidad_id=unidad_id)
    )


def asignar(session, bien_id, oficial_id):
    session.exec(
        text(
            "UPDATE bien SET oficial_id = :oficial_id, ubicacion_id = NULL "
            "WHERE id = :bien_id"
        ).bindparams(oficial_id=oficial_id, bien_id=bien_id)
    )


def registrar_dotacion(session, movimiento_id, oficial_id):
    session.exec(
        text(
            "INSERT INTO movimiento (id, tipo, estado, estado_revision, numero_acta, "
            "fecha_hecho, usuario_id, unidad_registrante_id, unidad_origen_id, "
            "unidad_destino_id, oficial_destino_id) VALUES (:id, 'ENTREGA', "
            "'APLICADO', 'PENDIENTE', '0002/2026', CURDATE(), 1, 4, 4, 4, :oficial)"
        ).bindparams(id=movimiento_id, oficial=oficial_id)
    )


def registrar_movimiento_de_traslado(session, id, oficial_id, origen, destino, bienes):
    session.exec(
        text(
            "INSERT INTO movimiento (id, tipo, estado, estado_revision, numero_acta, "
            "fecha_hecho, usuario_id, unidad_registrante_id, unidad_origen_id, "
            "oficial_origen_id, unidad_destino_id, oficial_destino_id) VALUES (:id, "
            "'TRASLADO', 'APLICADO', 'PENDIENTE', '0003/2026', CURDATE(), 1, :origen, "
            ":origen, :oficial, :destino, :oficial)"
        ).bindparams(id=id, origen=origen, oficial=oficial_id, destino=destino)
    )
    insertar_renglones(session, id, bienes)


def trasladar(session, id, oficial_id, origen, destino, estado="CONFIRMADO", bienes=()):
    if bienes:
        registrar_movimiento_de_traslado(
            session, id, oficial_id, origen, destino, bienes
        )
    session.exec(
        text(
            "INSERT INTO traslado_oficial (id, oficial_id, unidad_origen_id, "
            "unidad_destino_id, movimiento_id, estado, usuario_solicitante_id, "
            "usuario_resolucion_id, fecha_resolucion) VALUES (:id, :oficial, "
            ":origen, :destino, :movimiento, :estado, 1, "
            "IF(:estado = 'PENDIENTE', NULL, 1), "
            "IF(:estado = 'PENDIENTE', NULL, NOW()))"
        ).bindparams(
            id=id,
            oficial=oficial_id,
            origen=origen,
            destino=destino,
            movimiento=id if bienes else None,
            estado=estado,
        )
    )


def cambiar_unidad(session, oficial_id, unidad_id):
    session.exec(
        text("UPDATE oficial SET unidad_id = :unidad WHERE id = :id").bindparams(
            unidad=unidad_id, id=oficial_id
        )
    )


@pytest.fixture
def oficial_de_a(session, organizacion):
    insertar_oficial(session, 1, 4)


def test_un_oficial_sin_bienes_ni_movimientos_cambia_de_unidad(session, oficial_de_a):
    cambiar_unidad(session, 1, 5)

    unidad = session.exec(text("SELECT unidad_id FROM oficial WHERE id = 1"))
    assert unidad.scalar_one() == 5


def test_un_oficial_con_bienes_no_cambia_de_unidad_sin_traslado(session, oficial_de_a):
    asignar(session, 1, 1)

    with pytest.raises(OperationalError, match="traslado confirmado"):
        cambiar_unidad(session, 1, 5)


def test_un_oficial_con_movimientos_no_cambia_de_unidad_sin_traslado(
    session, oficial_de_a
):
    registrar_dotacion(session, 1, 1)

    with pytest.raises(OperationalError, match="traslado confirmado"):
        cambiar_unidad(session, 1, 5)


def test_un_traslado_pendiente_no_habilita_el_cambio_de_unidad(session, oficial_de_a):
    asignar(session, 1, 1)
    trasladar(session, 1, 1, 4, 5, estado="PENDIENTE")

    with pytest.raises(OperationalError, match="traslado confirmado"):
        cambiar_unidad(session, 1, 5)


def test_un_traslado_confirmado_cambia_la_unidad_y_mueve_sus_bienes(
    session, oficial_de_a
):
    asignar(session, 1, 1)
    trasladar(session, 1, 1, 4, 5, bienes=[1])

    cambiar_unidad(session, 1, 5)

    unidad = session.exec(text("SELECT unidad_id FROM bien WHERE id = 1"))
    assert unidad.scalar_one() == 5


def test_un_traslado_viejo_no_habilita_un_cambio_directo(session, oficial_de_a):
    asignar(session, 1, 1)
    trasladar(session, 1, 1, 4, 5, bienes=[1])
    cambiar_unidad(session, 1, 5)
    trasladar(session, 2, 1, 5, 4, bienes=[1])
    cambiar_unidad(session, 1, 4)

    with pytest.raises(OperationalError, match="traslado confirmado"):
        cambiar_unidad(session, 1, 5)


def test_un_oficial_trasladado_no_vuelve_con_un_cambio_directo(session, oficial_de_a):
    trasladar(session, 1, 1, 4, 5)
    cambiar_unidad(session, 1, 5)

    with pytest.raises(OperationalError, match="traslado confirmado"):
        cambiar_unidad(session, 1, 4)


def test_un_oficial_sin_dotaciones_cambia_por_un_traslado_sin_movimiento(
    session, oficial_de_a
):
    trasladar(session, 1, 1, 4, 5)

    cambiar_unidad(session, 1, 5)

    unidad = session.exec(text("SELECT unidad_id FROM oficial WHERE id = 1"))
    assert unidad.scalar_one() == 5


def test_un_traslado_sin_movimiento_no_mueve_dotaciones(session, oficial_de_a):
    trasladar(session, 1, 1, 4, 5)
    asignar(session, 1, 1)

    with pytest.raises(OperationalError, match="traslado confirmado"):
        cambiar_unidad(session, 1, 5)


def test_un_traslado_no_mueve_un_bien_que_no_esta_en_su_movimiento(
    session, oficial_de_a
):
    asignar(session, 1, 1)
    trasladar(session, 1, 1, 4, 5, bienes=[1])
    asignar(session, 2, 1)

    with pytest.raises(OperationalError, match="traslado confirmado"):
        cambiar_unidad(session, 1, 5)


def test_cambiar_otro_dato_de_un_oficial_con_bienes_se_acepta(session, oficial_de_a):
    asignar(session, 1, 1)

    session.exec(text("UPDATE oficial SET activo = FALSE WHERE id = 1"))

    activo = session.exec(text("SELECT activo FROM oficial WHERE id = 1"))
    assert activo.scalar_one() == 0


def cargar_informe(session, id):
    session.exec(
        text(
            "INSERT INTO documento (id, nombre_original, tipo_mime, tamano_bytes, "
            "hash_sha256, ruta_almacenamiento, usuario_id) VALUES (:id, 'informe.pdf', "
            "'application/pdf', 1024, SHA2(:id, 256), 'informes/x.pdf', 1)"
        ).bindparams(id=id)
    )


def registrar_salida_de_servicio(session, cambio_id, bien_id, documento_id):
    session.exec(
        text(
            "INSERT INTO cambio_estado_operativo (id, bien_id, estado_anterior, "
            "estado_nuevo, observaciones, documento_id, estado_revision, usuario_id, "
            "unidad_registrante_id) VALUES (:id, :bien_id, 'EN_SERVICIO', "
            "'FUERA_DE_SERVICIO', 'Falla en el percutor', :documento, 'PENDIENTE', "
            "1, 4)"
        ).bindparams(id=cambio_id, bien_id=bien_id, documento=documento_id)
    )


def test_rectificar_una_salida_de_servicio_sin_informe_es_rechazado(
    session, organizacion
):
    cargar_informe(session, 1)
    registrar_salida_de_servicio(session, 1, 1, 1)

    with pytest.raises(OperationalError, match="informe tecnico"):
        rectificar_cambio_de_estado(session, 1, 1)


def test_rectificar_una_salida_de_servicio_con_otro_informe_se_acepta(
    session, organizacion
):
    cargar_informe(session, 1)
    cargar_informe(session, 2)
    registrar_salida_de_servicio(session, 1, 1, 1)

    rectificar_cambio_de_estado(session, 1, 1, documento_id=2)

    vigente = session.exec(
        text("SELECT documento_id FROM v_cambio_estado_vigente WHERE id = 1")
    )
    assert vigente.scalar_one() == 2


def test_rectificar_una_vuelta_a_servicio_sin_informe_se_acepta(session, organizacion):
    registrar_cambio_de_estado(session, 1, 1)

    rectificar_cambio_de_estado(session, 1, 1)

    vigente = session.exec(
        text("SELECT version_vigente FROM v_cambio_estado_vigente WHERE id = 1")
    )
    assert vigente.scalar_one() == 1


def anular_cambio_de_estado(session, cambio_id):
    session.exec(
        text(
            "UPDATE cambio_estado_operativo SET estado = 'ANULADO', "
            "anulado_por_id = 1, fecha_anulacion = NOW(), "
            "motivo_anulacion = 'Se cargó sobre el bien equivocado' WHERE id = :id"
        ).bindparams(id=cambio_id)
    )


def test_anular_un_cambio_de_estado_conserva_el_registro(session, organizacion):
    registrar_cambio_de_estado(session, 1, 1)

    anular_cambio_de_estado(session, 1)

    cambio = session.exec(
        text(
            "SELECT estado, observaciones, anulado_por_id, motivo_anulacion "
            "FROM cambio_estado_operativo WHERE id = 1"
        )
    ).one()
    assert tuple(cambio) == (
        "ANULADO",
        "Reparada por el armero",
        1,
        "Se cargó sobre el bien equivocado",
    )


def test_anular_un_cambio_de_estado_sin_motivo_es_rechazado(session, organizacion):
    registrar_cambio_de_estado(session, 1, 1)

    with pytest.raises(OperationalError, match="ck_cambio_anulacion"):
        session.exec(
            text(
                "UPDATE cambio_estado_operativo SET estado = 'ANULADO', "
                "anulado_por_id = 1, fecha_anulacion = NOW() WHERE id = 1"
            )
        )


def test_un_cambio_aplicado_con_datos_de_anulacion_es_rechazado(session, organizacion):
    registrar_cambio_de_estado(session, 1, 1)

    with pytest.raises(OperationalError, match="ck_cambio_anulacion"):
        session.exec(
            text(
                "UPDATE cambio_estado_operativo "
                "SET motivo_anulacion = 'Sin anular' WHERE id = 1"
            )
        )


def test_un_cambio_de_estado_anulado_sale_de_la_bandeja(session, organizacion):
    registrar_cambio_de_estado(session, 1, 1)
    en_la_bandeja = text(
        "SELECT COUNT(*) FROM v_bandeja_revision "
        "WHERE registro = 'CAMBIO_ESTADO' AND registro_id = 1"
    )
    assert session.exec(en_la_bandeja).scalar_one() == 1

    anular_cambio_de_estado(session, 1)

    assert session.exec(en_la_bandeja).scalar_one() == 0


def test_un_cambio_de_estado_anulado_sigue_en_el_historial(session, organizacion):
    registrar_cambio_de_estado(session, 1, 1)

    anular_cambio_de_estado(session, 1)

    estado = session.exec(
        text(
            "SELECT estado FROM v_historial_bien "
            "WHERE registro = 'CAMBIO_ESTADO' AND registro_id = 1"
        )
    )
    assert estado.scalar_one() == "ANULADO"


def recibir_acta(session, movimiento_id, resultado, motivo=None):
    session.exec(
        text(
            "INSERT INTO recepcion (movimiento_id, resultado, motivo, usuario_id) "
            "VALUES (:m, :resultado, :motivo, 1)"
        ).bindparams(m=movimiento_id, resultado=resultado, motivo=motivo)
    )


def test_un_acta_devuelta_bloquea_sus_bienes_para_otro_movimiento(
    session, organizacion
):
    entregar(session, 1, [1], estado="DEVUELTO")

    with pytest.raises(OperationalError, match="no admite otro"):
        entregar(session, 2, [1])


def test_un_acta_devuelta_no_bloquea_otros_bienes(session, organizacion):
    entregar(session, 1, [1], estado="DEVUELTO")

    entregar(session, 2, [2])


def test_solo_una_entrega_entre_unidades_puede_quedar_devuelta(session, organizacion):
    entregar(session, 1, [1], estado="DEVUELTO")
    reubicar(session, 2, [2])

    with pytest.raises(OperationalError, match="ck_mov_devuelto"):
        pasar_a(session, 2, "DEVUELTO")


def test_un_acta_se_puede_devolver_varias_veces(session, organizacion):
    entregar(session, 1, [1])

    recibir_acta(session, 1, "DEVUELTO", "No coincide")
    recibir_acta(session, 1, "DEVUELTO", "Sigue sin coincidir")

    assert session.exec(text("SELECT COUNT(*) FROM recepcion")).scalar_one() == 2


@pytest.mark.parametrize("final", ["ACEPTADO", "RECHAZADO"])
def test_un_acta_devuelta_se_resuelve_una_sola_vez(session, organizacion, final):
    entregar(session, 1, [1])
    recibir_acta(session, 1, "DEVUELTO", "No coincide")
    recibir_acta(session, 1, final, "Desistió" if final == "RECHAZADO" else None)

    with pytest.raises(IntegrityError):
        recibir_acta(session, 1, "ACEPTADO")


@pytest.mark.parametrize(
    ("resultado", "motivo"),
    [("DEVUELTO", None), ("RECHAZADO", None), ("ACEPTADO", "No corresponde")],
    ids=["devuelto_sin_motivo", "rechazado_sin_motivo", "aceptado_con_motivo"],
)
def test_el_motivo_de_la_recepcion_va_con_devuelto_y_rechazado(
    session, organizacion, resultado, motivo
):
    entregar(session, 1, [1])

    with pytest.raises(OperationalError, match="ck_recepcion_motivo"):
        recibir_acta(session, 1, resultado, motivo)


def test_una_novedad_no_se_repite_en_la_misma_recepcion(session, organizacion):
    entregar(session, 1, [1])
    recibir_acta(session, 1, "DEVUELTO", "No coincide")
    session.exec(text("INSERT INTO recepcion_novedad VALUES (1, 1)"))

    with pytest.raises(IntegrityError):
        session.exec(text("INSERT INTO recepcion_novedad VALUES (1, 1)"))
