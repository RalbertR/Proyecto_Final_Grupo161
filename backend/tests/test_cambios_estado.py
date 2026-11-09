import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from io import BytesIO

import pytest
from pypdf import PdfWriter
from sqlmodel import text

from app.cambios_estado import repository
from app.core.database import engine
from app.core.seguridad import crear_token
from app.documentos import service as documentos

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

UBICACIONES = [
    (1, 4, "Depósito"),
    (2, 5, "Depósito"),
    (3, 2, "Depósito"),
    (4, 1, "Depósito"),
]

BIENES = [
    (1, "RD-1", 4, None, 1, False, "EN_SERVICIO"),
    (2, "RD-2", 4, None, 1, False, "FUERA_DE_SERVICIO"),
    (3, "RD-3", 4, 1, None, False, "EN_SERVICIO"),
    (4, "RD-4", 5, None, 2, False, "EN_SERVICIO"),
    (5, "RD-5", 4, None, None, True, "EN_SERVICIO"),
    (6, "RD-6", 4, None, 1, False, "EN_SERVICIO"),
    (7, "RD-7", 2, None, 3, False, "EN_SERVICIO"),
    (8, "RD-8", 1, None, 4, False, "EN_SERVICIO"),
]


def crear_pdf(titulo="Informe técnico"):
    escritor = PdfWriter()
    escritor.add_blank_page(width=72, height=72)
    escritor.add_metadata({"/Title": titulo})
    salida = BytesIO()
    escritor.write(salida)
    return salida.getvalue()


PDF = crear_pdf()


@pytest.fixture
def datos(monkeypatch, tmp_path):
    monkeypatch.setattr(documentos, "DIRECTORIO_DOCUMENTOS", tmp_path)
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
                "VALUES (:id, :unidad_id, :nombre)"
            ),
            [
                {"id": id, "unidad_id": unidad_id, "nombre": nombre}
                for id, unidad_id, nombre in UBICACIONES
            ],
        )
        conexion.execute(
            text(
                "INSERT INTO oficial (id, legajo, apellido, nombre, unidad_id, activo) "
                "VALUES (1, '50123', 'Gómez', 'Laura', 4, TRUE)"
            )
        )
        conexion.execute(
            text(
                "INSERT INTO bien (id, tipo_bien, marca, modelo, numero_serie, "
                "unidad_id, oficial_id, ubicacion_id, de_baja, estado_operativo) "
                "VALUES (:id, 'EQUIPO_COMUNICACIONES', 'Motorola', 'DEP450', :serie, "
                ":unidad, :oficial, :ubicacion, :de_baja, :estado)"
            ),
            [
                {
                    "id": id,
                    "serie": serie,
                    "unidad": unidad,
                    "oficial": oficial,
                    "ubicacion": ubicacion,
                    "de_baja": de_baja,
                    "estado": estado,
                }
                for id, serie, unidad, oficial, ubicacion, de_baja, estado in BIENES
            ],
        )
        conexion.execute(
            text(
                "INSERT INTO movimiento (id, tipo, estado, estado_revision, "
                "numero_acta, fecha_hecho, usuario_id, unidad_registrante_id, "
                "unidad_origen_id, unidad_destino_id) VALUES "
                "(1, 'ENTREGA', 'PENDIENTE', 'PENDIENTE', '0001/2026', :fecha, "
                "4, 4, 4, 5)"
            ),
            {"fecha": date.today() - timedelta(days=1)},
        )
        conexion.execute(
            text(
                "INSERT INTO movimiento_bien (movimiento_id, bien_id, "
                "ubicacion_origen_id) VALUES (1, 6, 1)"
            )
        )
    return tmp_path


def con_token(usuario_id=4):
    return {"Authorization": f"Bearer {crear_token(usuario_id)}"}


def cambiar(
    client,
    bien_id,
    estado,
    observaciones="Se golpeó y no transmite",
    pdf=PDF,
    usuario_id=4,
):
    archivos = (
        {"informe": ("informe.pdf", pdf, "application/pdf")}
        if pdf is not None
        else None
    )
    return client.post(
        f"/api/bienes/{bien_id}/cambios-estado",
        data={"estado_nuevo": estado, "observaciones": observaciones},
        files=archivos,
        headers=con_token(usuario_id),
    )


def consultar(sql):
    with engine.connect() as conexion:
        return conexion.execute(text(sql)).mappings().all()


def estado_del_bien(bien_id):
    return consultar(f"SELECT estado_operativo FROM bien WHERE id = {bien_id}")[0][
        "estado_operativo"
    ]


def en_simultaneo(*pedidos):
    conexiones = [engine.connect() for _ in pedidos]
    for conexion in conexiones:
        conexion.close()
    barrera = threading.Barrier(len(pedidos))

    def pedir(pedido):
        barrera.wait()
        return pedido()

    with ThreadPoolExecutor(len(pedidos)) as hilos:
        return list(hilos.map(pedir, pedidos, timeout=10))


def test_pasar_a_fuera_de_servicio_con_informe_cambia_el_bien_y_queda_en_el_historial(
    client, datos
):
    respuesta = cambiar(client, 1, "FUERA_DE_SERVICIO")

    assert respuesta.status_code == 201
    cambio = respuesta.json()
    assert cambio["estado_anterior"] == "EN_SERVICIO"
    assert cambio["estado_nuevo"] == "FUERA_DE_SERVICIO"
    assert cambio["observaciones"] == "Se golpeó y no transmite"
    assert cambio["informe"]["nombre_original"] == "informe.pdf"
    assert cambio["estado_revision"] == "PENDIENTE"
    assert cambio["bien"]["identificacion"] == "RD-1"
    assert cambio["unidad_registrante"] == "Unidad Operacional A"
    assert estado_del_bien(1) == "FUERA_DE_SERVICIO"
    historial = client.get("/api/bienes/1/historial", headers=con_token()).json()
    assert [
        evento["estado_operativo_nuevo"]
        for evento in historial["eventos"]
        if evento["registro"] == "CAMBIO_ESTADO"
    ] == ["FUERA_DE_SERVICIO"]


def test_volver_a_servicio_sin_informe(client, datos):
    respuesta = cambiar(client, 2, "EN_SERVICIO", "Se cambió la batería", pdf=None)

    assert respuesta.status_code == 201
    assert respuesta.json()["informe"] is None
    assert estado_del_bien(2) == "EN_SERVICIO"


def test_volver_a_servicio_con_informe(client, datos):
    respuesta = cambiar(client, 2, "EN_SERVICIO", "Se cambió la batería")

    assert respuesta.status_code == 201
    assert respuesta.json()["informe"] is not None


def test_fuera_de_servicio_sin_informe_responde_422(client, datos):
    respuesta = cambiar(client, 1, "FUERA_DE_SERVICIO", pdf=None)

    assert respuesta.status_code == 422
    assert consultar("SELECT id FROM cambio_estado_operativo") == []
    assert estado_del_bien(1) == "EN_SERVICIO"


@pytest.mark.parametrize(
    ("bien_id", "estado"), [(1, "FUERA_DE_SERVICIO"), (2, "EN_SERVICIO")]
)
def test_sin_observaciones_responde_422(client, datos, bien_id, estado):
    respuesta = cambiar(client, bien_id, estado, observaciones="   ")

    assert respuesta.status_code == 422
    assert consultar("SELECT id FROM cambio_estado_operativo") == []


def test_bien_de_otra_unidad_responde_403(client, datos):
    assert cambiar(client, 4, "FUERA_DE_SERVICIO").status_code == 403
    assert estado_del_bien(4) == "EN_SERVICIO"


def test_bien_inexistente_responde_404(client, datos):
    assert cambiar(client, 99, "FUERA_DE_SERVICIO").status_code == 404


def test_bien_en_dotacion_cambia_y_sigue_asignado(client, datos):
    respuesta = cambiar(client, 3, "FUERA_DE_SERVICIO")

    assert respuesta.status_code == 201
    [bien] = consultar("SELECT oficial_id, estado_operativo FROM bien WHERE id = 3")
    assert bien["oficial_id"] == 1
    assert bien["estado_operativo"] == "FUERA_DE_SERVICIO"


def test_bien_con_movimiento_pendiente_responde_409(client, datos):
    assert cambiar(client, 6, "FUERA_DE_SERVICIO").status_code == 409
    assert estado_del_bien(6) == "EN_SERVICIO"


def test_bien_de_baja_responde_409(client, datos):
    assert cambiar(client, 5, "FUERA_DE_SERVICIO").status_code == 409


def test_bien_que_ya_esta_en_ese_estado_responde_409(client, datos):
    assert cambiar(client, 1, "EN_SERVICIO", pdf=None).status_code == 409


def test_pdf_invalido_responde_422_y_no_guarda_nada(client, datos):
    respuesta = cambiar(client, 1, "FUERA_DE_SERVICIO", pdf=b"hola")

    assert respuesta.status_code == 422
    assert consultar("SELECT id FROM cambio_estado_operativo") == []
    assert consultar("SELECT id FROM documento") == []
    assert list(datos.iterdir()) == []


def test_lo_registrado_por_direccion_no_requiere_revision(client, datos):
    respuesta = cambiar(client, 8, "FUERA_DE_SERVICIO", usuario_id=1)

    assert respuesta.status_code == 201
    assert respuesta.json()["estado_revision"] == "NO_APLICA"
    for usuario_id in (1, 2, 3):
        bandeja = client.get(
            "/api/revisiones/bandeja", headers=con_token(usuario_id)
        ).json()
        assert [r for r in bandeja if r["registro"] == "CAMBIO_ESTADO"] == []


def test_lo_registrado_por_una_regional_va_a_la_bandeja_de_direccion(client, datos):
    cambio = cambiar(client, 7, "FUERA_DE_SERVICIO", usuario_id=2).json()

    bandeja = client.get("/api/revisiones/bandeja", headers=con_token(1)).json()
    assert [r["registro_id"] for r in bandeja if r["registro"] == "CAMBIO_ESTADO"] == [
        cambio["id"]
    ]


def test_un_fallo_al_registrar_borra_el_pdf_guardado(client, datos, monkeypatch):
    def fallar(*args, **kwargs):
        raise OSError("disco lleno")

    monkeypatch.setattr(repository, "insertar_cambio", fallar)

    respuesta = cambiar(client, 1, "FUERA_DE_SERVICIO")

    assert respuesta.status_code == 503
    assert consultar("SELECT id FROM documento") == []
    assert list(datos.iterdir()) == []
    assert estado_del_bien(1) == "EN_SERVICIO"


def test_dos_cambios_simultaneos_del_mismo_bien(client, datos):
    uno, dos = crear_pdf("uno"), crear_pdf("dos")

    respuestas = en_simultaneo(
        lambda: cambiar(client, 1, "FUERA_DE_SERVICIO", pdf=uno),
        lambda: cambiar(client, 1, "FUERA_DE_SERVICIO", pdf=dos),
    )

    assert sorted(r.status_code for r in respuestas) == [201, 409]
    assert len(consultar("SELECT id FROM cambio_estado_operativo")) == 1
    assert len(consultar("SELECT id FROM documento")) == 1
    assert len(list(datos.iterdir())) == 1
    assert estado_del_bien(1) == "FUERA_DE_SERVICIO"


def test_ver_el_cambio_y_su_informe(client, datos):
    cambio_id = cambiar(client, 1, "FUERA_DE_SERVICIO").json()["id"]

    for usuario_id in (4, 2, 1):
        respuesta = client.get(
            f"/api/cambios-estado/{cambio_id}", headers=con_token(usuario_id)
        )
        assert respuesta.status_code == 200
        assert respuesta.json()["id"] == cambio_id
    assert (
        client.get(f"/api/cambios-estado/{cambio_id}", headers=con_token(6)).status_code
        == 403
    )
    informe = client.get(
        f"/api/cambios-estado/{cambio_id}/informe", headers=con_token(2)
    )
    assert informe.status_code == 200
    assert informe.content == PDF
    assert informe.headers["content-type"] == "application/pdf"
    assert (
        client.get(
            f"/api/cambios-estado/{cambio_id}/informe", headers=con_token(6)
        ).status_code
        == 403
    )


def test_la_registrante_y_la_duena_nueva_ven_un_cambio_de_un_bien_entregado(
    client, datos
):
    cambio_id = cambiar(client, 1, "FUERA_DE_SERVICIO").json()["id"]
    with engine.begin() as conexion:
        conexion.execute(
            text("UPDATE bien SET unidad_id = 5, ubicacion_id = 2 WHERE id = 1")
        )

    for usuario_id in (4, 5):
        assert (
            client.get(
                f"/api/cambios-estado/{cambio_id}/informe",
                headers=con_token(usuario_id),
            ).status_code
            == 200
        )
    assert (
        client.get(f"/api/cambios-estado/{cambio_id}", headers=con_token(6)).status_code
        == 403
    )


def test_cambio_inexistente_responde_404(client, datos):
    assert client.get("/api/cambios-estado/99", headers=con_token()).status_code == 404


def test_informe_de_un_cambio_sin_informe_responde_404(client, datos):
    cambio_id = cambiar(client, 2, "EN_SERVICIO", "Reparado", pdf=None).json()["id"]

    respuesta = client.get(
        f"/api/cambios-estado/{cambio_id}/informe", headers=con_token()
    )

    assert respuesta.status_code == 404
