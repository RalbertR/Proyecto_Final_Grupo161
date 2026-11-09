from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from threading import Barrier
from uuid import UUID

import pytest
from pypdf import PdfWriter
from sqlmodel import text

from app.core.database import engine
from app.core.seguridad import crear_token
from app.documentos import service

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
    (7, "otro.aux.unidad_a", 4),
]

LIMITE = 10 * 1024 * 1024


def crear_pdf(titulo="Acta firmada"):
    escritor = PdfWriter()
    escritor.add_blank_page(width=72, height=72)
    escritor.add_metadata({"/Title": titulo})
    salida = BytesIO()
    escritor.write(salida)
    return salida.getvalue()


PDF = crear_pdf()


@pytest.fixture
def actas(monkeypatch, tmp_path):
    monkeypatch.setattr(service, "DIRECTORIO_DOCUMENTOS", tmp_path)
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
                "INSERT INTO movimiento (id, tipo, estado, estado_revision, "
                "numero_acta, fecha_hecho, usuario_id, unidad_registrante_id, "
                "unidad_origen_id, unidad_destino_id) VALUES "
                "(:id, 'ENTREGA', 'APLICADO', 'PENDIENTE', :numero, "
                ":fecha, 4, 4, 4, 5)"
            ),
            [
                {
                    "id": id,
                    "numero": f"{id:04}/2026",
                    "fecha": date.today() - timedelta(days=1),
                }
                for id in (1, 2)
            ],
        )
    return tmp_path


def con_token(usuario_id=4):
    return {"Authorization": f"Bearer {crear_token(usuario_id)}"}


def adjuntar(client, contenido=PDF, nombre="acta firmada.pdf", usuario_id=4, acta_id=1):
    return client.post(
        f"/api/movimientos/{acta_id}/documentos",
        files={"archivo": (nombre, contenido, "application/pdf")},
        headers=con_token(usuario_id),
    )


def listar(client, usuario_id=4, acta_id=1):
    return client.get(
        f"/api/movimientos/{acta_id}/documentos", headers=con_token(usuario_id)
    )


def descargar(client, documento_id, usuario_id=4, acta_id=1):
    return client.get(
        f"/api/movimientos/{acta_id}/documentos/{documento_id}",
        headers=con_token(usuario_id),
    )


def consultar(sql):
    with engine.connect() as conexion:
        return conexion.execute(text(sql)).mappings().all()


def test_adjuntar_guarda_el_pdf_y_sus_metadatos_asociados_al_acta(client, actas):
    respuesta = adjuntar(client)

    assert respuesta.status_code == 201
    documento = respuesta.json()
    assert documento["nombre_original"] == "acta firmada.pdf"
    assert documento["tipo_mime"] == "application/pdf"
    assert documento["tamano_bytes"] == len(PDF)
    assert documento["hash_sha256"] == sha256(PDF).hexdigest()
    assert documento["usuario"] == "aux.unidad_a"
    assert datetime.fromisoformat(documento["fecha_carga"])
    assert "ruta_almacenamiento" not in documento
    [guardado] = consultar("SELECT * FROM documento")
    assert guardado["usuario_id"] == 4
    assert guardado["nombre_original"] == documento["nombre_original"]
    assert guardado["tamano_bytes"] == len(PDF)
    assert guardado["hash_sha256"] == documento["hash_sha256"]
    assert guardado["reemplaza_documento_id"] is None
    assert consultar("SELECT * FROM movimiento_documento") == [
        {"movimiento_id": 1, "documento_id": documento["id"]}
    ]
    [archivo] = list(actas.iterdir())
    assert archivo.name != documento["nombre_original"]
    assert UUID(archivo.stem)
    assert archivo.read_bytes() == PDF
    assert Path(guardado["ruta_almacenamiento"]).name == archivo.name
    assert listar(client).json() == {
        "documentos": [documento],
        "puede_adjuntar": True,
    }


def test_un_acta_sin_documentos_devuelve_la_lista_vacia(client, actas):
    respuesta = listar(client)

    assert respuesta.status_code == 200
    assert respuesta.json() == {"documentos": [], "puede_adjuntar": True}
    assert list(actas.iterdir()) == []


def test_el_acta_admite_varios_pdfs_distintos_sin_reemplazar_el_primero(client, actas):
    primero = adjuntar(client).json()
    otro_pdf = crear_pdf("Anexo firmado")

    respuesta = adjuntar(client, contenido=otro_pdf, nombre="anexo.pdf")

    assert respuesta.status_code == 201
    assert listar(client).json()["documentos"] == [primero, respuesta.json()]
    assert descargar(client, primero["id"]).content == PDF
    assert descargar(client, respuesta.json()["id"]).content == otro_pdf
    assert len(list(actas.iterdir())) == 2
    assert all(
        documento["reemplaza_documento_id"] is None
        for documento in consultar("SELECT * FROM documento")
    )


def test_otro_usuario_de_la_unidad_registrante_puede_adjuntar(client, actas):
    respuesta = adjuntar(client, usuario_id=7)

    assert respuesta.status_code == 201
    assert respuesta.json()["usuario"] == "otro.aux.unidad_a"
    assert consultar("SELECT usuario_id FROM documento") == [{"usuario_id": 7}]


@pytest.mark.parametrize(
    "usuario_id", [4, 5, 2, 1], ids=["origen", "destino", "regional", "direccion"]
)
def test_quien_consulta_el_acta_lista_y_descarga_sus_documentos(
    client, actas, usuario_id
):
    documento = adjuntar(client).json()

    listado = listar(client, usuario_id)
    descarga = descargar(client, documento["id"], usuario_id)

    assert listado.status_code == 200
    assert listado.json() == {
        "documentos": [documento],
        "puede_adjuntar": usuario_id == 4,
    }
    assert descarga.status_code == 200
    assert descarga.content == PDF
    assert descarga.headers["content-type"] == "application/pdf"
    assert descarga.headers["content-length"] == str(len(PDF))
    assert descarga.headers["content-disposition"].startswith("attachment;")
    assert "acta%20firmada.pdf" in descarga.headers["content-disposition"]
    assert descarga.headers["cache-control"] == "private, no-store"
    assert descarga.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize(
    "usuario_id", [1, 2, 5, 6], ids=["direccion", "regional", "destino", "ajeno"]
)
def test_solo_la_unidad_que_registro_el_acta_adjunta(client, actas, usuario_id):
    respuesta = adjuntar(client, usuario_id=usuario_id)

    assert respuesta.status_code == 403
    assert consultar("SELECT * FROM documento") == []
    assert consultar("SELECT * FROM movimiento_documento") == []
    assert list(actas.iterdir()) == []


@pytest.mark.parametrize(
    "usuario_id", [3, 6], ids=["otra_regional", "otra_operacional"]
)
def test_fuera_del_alcance_no_lista_ni_descarga_el_pdf(client, actas, usuario_id):
    documento_id = adjuntar(client).json()["id"]

    assert listar(client, usuario_id).status_code == 403
    assert descargar(client, documento_id, usuario_id).status_code == 403
    assert descargar(client, 999, usuario_id).status_code == 403


def test_los_documentos_requieren_una_sesion(client, actas):
    assert client.get("/api/movimientos/1/documentos").status_code == 401
    assert client.get("/api/movimientos/1/documentos/1").status_code == 401
    respuesta = client.post(
        "/api/movimientos/1/documentos",
        files={"archivo": ("acta.pdf", PDF, "application/pdf")},
    )
    assert respuesta.status_code == 401
    assert consultar("SELECT * FROM documento") == []
    assert list(actas.iterdir()) == []


def test_un_movimiento_inexistente_responde_404_sin_guardar_el_archivo(client, actas):
    assert listar(client, acta_id=999).status_code == 404
    assert adjuntar(client, acta_id=999).status_code == 404
    assert descargar(client, 1, acta_id=999).status_code == 404
    assert consultar("SELECT * FROM documento") == []
    assert list(actas.iterdir()) == []


def test_no_se_descarga_un_documento_de_otra_acta_o_inexistente(client, actas):
    documento_id = adjuntar(client).json()["id"]

    assert descargar(client, documento_id, acta_id=2).status_code == 404
    assert descargar(client, 999).status_code == 404


@pytest.mark.parametrize("acta_id", [1, 2], ids=["misma_acta", "otra_acta"])
def test_el_mismo_pdf_no_se_duplica_aunque_cambie_el_nombre(client, actas, acta_id):
    documento = adjuntar(client).json()

    respuesta = adjuntar(client, nombre="otro nombre.pdf", acta_id=acta_id)

    assert respuesta.status_code == 409
    assert len(consultar("SELECT * FROM documento")) == 1
    assert consultar("SELECT * FROM movimiento_documento") == [
        {"movimiento_id": 1, "documento_id": documento["id"]}
    ]
    [archivo] = list(actas.iterdir())
    assert archivo.read_bytes() == PDF


@pytest.mark.parametrize(
    "contenido,nombre,mime",
    [
        (b"", "acta.pdf", "application/pdf"),
        (b"Esto no es un PDF", "acta.pdf", "application/pdf"),
        (b"%PDF-1.4\ntexto sin estructura PDF\n%%EOF", "acta.pdf", "application/pdf"),
        (PDF[:100], "acta.pdf", "application/pdf"),
        (PDF, "acta.txt", "application/pdf"),
        (PDF, "acta.pdf", "text/plain"),
        (PDF, f"{'a' * 252}.pdf", "application/pdf"),
    ],
    ids=[
        "vacio",
        "texto_disfrazado",
        "firma_falsa",
        "truncado",
        "extension",
        "mime",
        "nombre_largo",
    ],
)
def test_un_archivo_invalido_responde_422_sin_persistir_nada(
    client, actas, contenido, nombre, mime
):
    respuesta = client.post(
        "/api/movimientos/1/documentos",
        files={"archivo": (nombre, contenido, mime)},
        headers=con_token(),
    )

    assert respuesta.status_code == 422
    assert consultar("SELECT * FROM documento") == []
    assert consultar("SELECT * FROM movimiento_documento") == []
    assert list(actas.iterdir()) == []


def test_un_pdf_que_requiere_contrasena_responde_422(client, actas):
    escritor = PdfWriter()
    escritor.add_blank_page(width=72, height=72)
    escritor.encrypt("clave_del_acta")
    salida = BytesIO()
    escritor.write(salida)

    respuesta = adjuntar(client, contenido=salida.getvalue())

    assert respuesta.status_code == 422
    assert consultar("SELECT * FROM documento") == []
    assert list(actas.iterdir()) == []


def pdf_de_tamano(tamano):
    # Un comentario entre el trailer y startxref conserva todos los offsets.
    relleno = b"%" + b"x" * (tamano - len(PDF) - 2) + b"\n"
    return PDF.replace(b"startxref\n", relleno + b"startxref\n")


@pytest.mark.parametrize(
    "tamano,estado",
    [(LIMITE, 201), (LIMITE + 1, 422)],
    ids=["limite_exacto", "un_byte_de_mas"],
)
def test_el_limite_del_pdf_se_controla_con_los_bytes_reales(
    client, actas, tamano, estado
):
    contenido = pdf_de_tamano(tamano)
    assert len(contenido) == tamano

    respuesta = adjuntar(client, contenido=contenido)

    assert respuesta.status_code == estado
    if estado == 201:
        assert respuesta.json()["tamano_bytes"] == LIMITE
        assert respuesta.json()["hash_sha256"] == sha256(contenido).hexdigest()
        assert descargar(client, respuesta.json()["id"]).content == contenido
    else:
        assert consultar("SELECT * FROM documento") == []
        assert list(actas.iterdir()) == []


@pytest.mark.parametrize("nombre", ["../../acta.pdf", r"C:\documentos\acta.pdf"])
def test_un_nombre_con_directorios_se_guarda_solo_como_nombre_original(
    client, actas, nombre
):
    respuesta = adjuntar(client, nombre=nombre)

    assert respuesta.status_code == 201
    assert respuesta.json()["nombre_original"] == "acta.pdf"
    [archivo] = list(actas.iterdir())
    assert UUID(archivo.stem)
    assert archivo.read_bytes() == PDF
    descarga = descargar(client, respuesta.json()["id"])
    assert descarga.headers["content-disposition"] == 'attachment; filename="acta.pdf"'


def test_el_tenedor_actual_descarga_un_acta_anterior_y_pierde_acceso_al_dejar_de_tener_el_bien(
    client, actas
):
    documento_id = adjuntar(client).json()["id"]
    with engine.begin() as conexion:
        conexion.execute(
            text(
                "INSERT INTO ubicacion (id, unidad_id, nombre) VALUES "
                "(1, 6, 'Sala de Armas'), (2, 5, 'Sala de Armas')"
            )
        )
        conexion.execute(
            text(
                "INSERT INTO bien (id, tipo_bien, marca, modelo, numero_serie, "
                "unidad_id, ubicacion_id) VALUES "
                "(1, 'ARMAMENTO', 'Bersa', 'TPR9', 'BT-1', 6, 1)"
            )
        )
        conexion.execute(
            text("INSERT INTO movimiento_bien (movimiento_id, bien_id) VALUES (1, 1)")
        )

    listado = listar(client, usuario_id=6)
    assert listado.status_code == 200
    assert listado.json()["puede_adjuntar"] is False
    assert descargar(client, documento_id, usuario_id=6).content == PDF
    assert (
        adjuntar(client, contenido=crear_pdf("Otro"), usuario_id=6).status_code == 403
    )

    with engine.begin() as conexion:
        conexion.execute(
            text("UPDATE bien SET unidad_id = 5, ubicacion_id = 2 WHERE id = 1")
        )

    assert listar(client, usuario_id=6).status_code == 403
    assert descargar(client, documento_id, usuario_id=6).status_code == 403


def test_dos_cargas_simultaneas_del_mismo_pdf_guardan_un_solo_documento(
    client, actas, monkeypatch
):
    barrera = Barrier(2)
    hash_cargado = service.repository.hash_cargado

    def esperar_ambas_consultas(*args, **kwargs):
        cargado = hash_cargado(*args, **kwargs)
        # Ambas peticiones pasan el prechequeo: la duplicación la evita el índice.
        barrera.wait(timeout=10)
        return cargado

    monkeypatch.setattr(service.repository, "hash_cargado", esperar_ambas_consultas)

    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        respuestas = list(
            ejecutor.map(lambda acta_id: adjuntar(client, acta_id=acta_id), [1, 2])
        )

    assert sorted(respuesta.status_code for respuesta in respuestas) == [201, 409]
    assert len(consultar("SELECT * FROM documento")) == 1
    assert len(consultar("SELECT * FROM movimiento_documento")) == 1
    [archivo] = list(actas.iterdir())
    assert archivo.read_bytes() == PDF


def test_si_falla_la_asociacion_se_revierte_el_documento_y_se_borra_el_archivo(
    client, actas, monkeypatch
):
    def fallar(*args, **kwargs):
        raise RuntimeError("No se pudo asociar el documento")

    monkeypatch.setattr(service.repository, "vincular_documento", fallar)

    with pytest.raises(RuntimeError, match="No se pudo asociar"):
        adjuntar(client)

    assert consultar("SELECT * FROM documento") == []
    assert consultar("SELECT * FROM movimiento_documento") == []
    assert list(actas.iterdir()) == []


def test_si_no_se_puede_crear_el_archivo_no_se_guardan_metadatos(
    client, actas, monkeypatch
):
    def fallar(*args, **kwargs):
        raise OSError("Sin espacio en disco")

    monkeypatch.setattr(service.os, "open", fallar)

    respuesta = adjuntar(client)

    assert respuesta.status_code == 503
    assert consultar("SELECT * FROM documento") == []
    assert list(actas.iterdir()) == []


def test_si_la_escritura_falla_no_queda_un_pdf_parcial(client, actas, monkeypatch):
    abrir_descriptor = service.os.fdopen

    class EscrituraFallida:
        def __init__(self, descriptor, modo):
            self.archivo = abrir_descriptor(descriptor, modo)

        def __enter__(self):
            return self

        def write(self, contenido):
            self.archivo.write(contenido[:8])
            raise OSError("Sin espacio en disco")

        def __exit__(self, *args):
            self.archivo.close()

    monkeypatch.setattr(service.os, "fdopen", EscrituraFallida)

    respuesta = adjuntar(client)

    assert respuesta.status_code == 503
    assert consultar("SELECT * FROM documento") == []
    assert list(actas.iterdir()) == []


def test_un_archivo_que_ya_no_esta_disponible_responde_404(client, actas):
    documento_id = adjuntar(client).json()["id"]
    [archivo] = list(actas.iterdir())
    archivo.unlink()

    assert descargar(client, documento_id).status_code == 404


def test_una_ruta_guardada_fuera_del_directorio_privado_no_se_descarga(client, actas):
    documento_id = adjuntar(client).json()["id"]
    archivo_externo = actas.parent / f"{actas.name}.pdf"
    archivo_externo.write_bytes(crear_pdf("Documento ajeno"))
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text("UPDATE documento SET ruta_almacenamiento = :ruta"),
                {"ruta": f"../{archivo_externo.name}"},
            )

        assert descargar(client, documento_id).status_code == 404
    finally:
        archivo_externo.unlink()
