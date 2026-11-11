"""Carga una historia de julio a noviembre de 2026 para la demostración.

Se corre después de cargar_datos_prueba.py y cargar_demo.py, con el backend levantado:

    docker compose run --rm semillas python /semillas/cargar_historia.py historia
    docker compose run --rm semillas python /semillas/cargar_historia.py cerrar

`historia` registra por la API (respeta reglas y triggers) entregas, recepciones,
devoluciones, rechazos, revisiones, observaciones, rectificaciones, dotaciones y
cambios de estado de servicio, en orden cronológico. Después de cada llamada fecha
el registro con la fecha simulada, por SQL.

`cerrar` ajusta las fechas de lo que cargó cargar_demo.py, numera las actas de cada
unidad en orden cronológico, adjunta el acta escaneada de cada una y muestra el
resumen de lo que ve cada usuario.
"""

import json
import os
import random
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta

from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cargar_demo import BASE, USUARIOS, Demo, Fallo, llamar
from pdf_minimo import crear_pdf

ARM, CHA, MOV, EQP = (
    ["ARMAMENTO"],
    ["CHALECO"],
    ["MOVIL"],
    ["EQUIPO_COMUNICACIONES"],
)
AREA_SEGURIDAD = ARM + CHA
SUPERIOR = {
    "a": "norte",
    "b": "norte",
    "c": "sur",
    "norte": "direccion",
    "sur": "direccion",
}
NOMBRE_UNIDAD = {
    "direccion": "Dirección Logística",
    "norte": "Unidad Regional Norte",
    "sur": "Unidad Regional Sur",
    "a": "Unidad Operacional A",
    "b": "Unidad Operacional B",
    "c": "Unidad Operacional C",
}
NUMERO_INICIAL = {"direccion": 14, "norte": 9, "sur": 8, "a": 24, "b": 17, "c": 12}
NUMERO_DE_PRUEBA = 500
MINIMO = datetime(2000, 1, 1)

DESCRIPCIONES = {
    "seguridad": [
        "Reposición de armamento y chalecos para el servicio de calle",
        "Redistribución de armamento por cambio de dotación",
        "Provisión de equipamiento de seguridad para el turno noche",
        "Refuerzo de la dotación por aumento del patrullaje",
    ],
    "movilidad": [
        "Equipamiento para móviles de patrullaje",
        "Redistribución de equipos de comunicaciones",
        "Asignación de móvil para traslados y diligencias",
        "Equipos para reemplazar los que están en reparación",
    ],
}
OBSERVACIONES = {
    "fecha": (
        "La fecha del hecho no coincide con la del acta escaneada",
        "Se corrigió la fecha del hecho según el acta firmada",
    ),
    "numero": (
        "El número de acta no coincide con el acta escaneada",
        "Se corrigió el número de acta, había un error de tipeo",
    ),
    "descripcion": (
        "La descripción no detalla los bienes del acta",
        "Se completó la descripción con el detalle de los bienes",
    ),
}
MOTIVOS_DEVOLUCION = [
    "El número de serie de un bien no coincide con el acta",
    "Falta un bien indicado en el acta",
    "Un bien llegó con daños visibles",
]
FALLAS = {
    "MOVIL": (
        "Falla en la caja de cambios, fuera de servicio hasta la reparación",
        "Reparado y verificado en el taller oficial, vuelve al servicio",
    ),
    "ARMAMENTO": (
        "Corredera fisurada, no apto para el uso",
        "Reparado por el armero de la Dirección, vuelve al servicio",
    ),
    "EQUIPO_COMUNICACIONES": (
        "Batería inutilizada y antena dañada",
        "Se reemplazó la batería y la antena, vuelve al servicio",
    ),
    "CHALECO": (
        "Paneles balísticos con daño por humedad",
        "Reemplazo de paneles certificado, vuelve al servicio",
    ),
}


def enviar(metodo, ruta, token, cuerpo, tipo_contenido, esperado=(200, 201)):
    cabeceras = {"Authorization": f"Bearer {token}", "Content-Type": tipo_contenido}
    pedido = urllib.request.Request(
        BASE + ruta, data=cuerpo, headers=cabeceras, method=metodo
    )
    try:
        with urllib.request.urlopen(pedido) as respuesta:
            codigo, texto = respuesta.status, respuesta.read()
    except urllib.error.HTTPError as error:
        codigo, texto = error.code, error.read()
    datos = json.loads(texto) if texto else None
    if codigo not in esperado:
        raise Fallo(f"{metodo} {ruta} respondió {codigo}: {datos}")
    return datos


def multipart(campos, archivo=None):
    limite = uuid.uuid4().hex
    partes = []
    for nombre, valor in campos.items():
        partes.append(
            f'--{limite}\r\nContent-Disposition: form-data; name="{nombre}"\r\n\r\n{valor}\r\n'.encode()
        )
    if archivo:
        campo, nombre_archivo, contenido = archivo
        partes.append(
            (
                f'--{limite}\r\nContent-Disposition: form-data; name="{campo}"; '
                f'filename="{nombre_archivo}"\r\nContent-Type: application/pdf\r\n\r\n'
            ).encode()
            + contenido
            + b"\r\n"
        )
    partes.append(f"--{limite}--\r\n".encode())
    return b"".join(partes), f"multipart/form-data; boundary={limite}"


def seguro(funcion):
    """Un evento que falla se avisa y la historia sigue con el siguiente."""

    def envoltura(*argumentos, **claves):
        try:
            return funcion(*argumentos, **claves)
        except Fallo as error:
            print(f"  !! {funcion.__name__} falló: {error}")

    envoltura.__name__ = funcion.__name__
    return envoltura


class Historia(Demo):
    def __init__(self):
        super().__init__()
        self.engine = create_engine(os.environ["DATABASE_URL"])
        self.azar = random.Random(161)
        self.ahora = self.consultar("SELECT NOW()")[0][0]
        self.informes = 0
        self.cuenta = NUMERO_DE_PRUEBA
        # Último momento en que se tocó cada bien: ningún evento nuevo puede
        # empezar antes, así el orden de aplicación sigue a las fechas.
        self.ultimo = {
            fila[0]: fila[1]
            for fila in self.consultar(
                "SELECT bien_id, MAX(f) FROM ("
                " SELECT mb.bien_id, GREATEST(m.fecha_carga, COALESCE(r.fecha, m.fecha_carga)) f"
                " FROM movimiento_bien mb JOIN movimiento m ON m.id = mb.movimiento_id"
                " LEFT JOIN recepcion r ON r.movimiento_id = m.id"
                " UNION ALL SELECT bien_id, fecha FROM cambio_estado_operativo"
                ") t GROUP BY bien_id"
            )
        }

    # ---- utilidades -------------------------------------------------------

    def consultar(self, sentencia, **parametros):
        with self.engine.connect() as conexion:
            return conexion.execute(text(sentencia), parametros).fetchall()

    def ejecutar(self, sentencia, **parametros):
        with self.engine.begin() as conexion:
            conexion.execute(text(sentencia), parametros)

    def T(self, mes, dia, hora=None):
        hora = hora if hora is not None else self.azar.randint(8, 14)
        return datetime(2026, mes, dia, hora, self.azar.randint(0, 59))

    def tope(self, momento):
        return min(momento, self.ahora - timedelta(hours=1))

    def despues(self, momento, minimo, maximo):
        dias = self.azar.randint(minimo, maximo)
        siguiente = momento + timedelta(days=dias)
        siguiente = siguiente.replace(
            hour=self.azar.randint(9, 16), minute=self.azar.randint(0, 59)
        )
        return self.tope(max(siguiente, momento))

    def descripcion(self, tipos, momento):
        area = "seguridad" if tipos[0] in ("ARMAMENTO", "CHALECO") else "movilidad"
        lista = DESCRIPCIONES[area]
        return lista[(momento.timetuple().tm_yday + self.cuenta) % len(lista)]

    def numero_de_prueba(self):
        self.cuenta += 1
        return f"{self.cuenta:04d}/2026"

    def elegir_h(
        self, quien, tipos, cantidad, inicio, tenencia="DEPOSITO", legajo=None
    ):
        elegidos = []
        inventario = self.pedir(quien, "GET", "/inventario")
        for tipo in tipos:
            for bien in inventario:
                if (
                    bien["unidad_id"] == self.unidad_id[quien]
                    and bien["tipo_bien"] == tipo
                    and bien["tenencia"] == tenencia
                    and bien["estado_operativo"] == "EN_SERVICIO"
                    and not bien["con_movimiento_pendiente"]
                    and self.ultimo.get(bien["bien_id"], MINIMO) < inicio
                    and (legajo is None or bien["oficial_legajo"] == legajo)
                ):
                    elegidos.append(bien)
        return elegidos[:cantidad]

    # ---- fechado ----------------------------------------------------------

    def fechar_movimiento(self, movimiento_id, momento):
        self.ejecutar(
            "UPDATE movimiento SET fecha_carga = :t WHERE id = :id",
            t=momento,
            id=movimiento_id,
        )

    def fechar_ultimo(
        self, tabla, columna_objeto, objeto_id, momento, columna_fecha="fecha"
    ):
        self.ejecutar(
            f"UPDATE {tabla} SET {columna_fecha} = :t WHERE {columna_objeto} = :id ORDER BY id DESC LIMIT 1",
            t=momento,
            id=objeto_id,
        )

    # ---- pasos de un acta -------------------------------------------------

    def crear_entrega(self, origen, destino, bienes, momento, tipos):
        hecho = momento.date()
        acta = self.pedir(
            origen,
            "POST",
            "/movimientos/entregas",
            {
                "numero_acta": self.numero_de_prueba(),
                "fecha_hecho": hecho.isoformat(),
                "descripcion": self.descripcion(tipos, momento),
                "bienes": [bien["bien_id"] for bien in bienes],
                "unidad_destino_id": self.unidad_id[destino],
            },
        )
        self.fechar_movimiento(acta["id"], momento)
        return acta["id"]

    def aceptar(self, receptor, movimiento_id, momento, bienes):
        acta = self.pedir(receptor, "GET", f"/movimientos/{movimiento_id}")
        propias = self.ubicaciones(receptor)
        ubicaciones = {
            "ARMAMENTO": "Sala de Armas",
            "CHALECO": "Sala de Armas",
            "EQUIPO_COMUNICACIONES": "Depósito",
            "MOVIL": "Playón",
        }
        self.pedir(
            receptor,
            "POST",
            f"/movimientos/{movimiento_id}/recepcion",
            {
                "resultado": "ACEPTADO",
                "ubicaciones": [
                    {
                        "bien_id": r["bien_id"],
                        "ubicacion_id": propias[ubicaciones[r["tipo_bien"]]],
                    }
                    for r in acta["bienes"]
                ],
            },
        )
        self.fechar_ultimo("recepcion", "movimiento_id", movimiento_id, momento)
        for bien in bienes:
            self.ultimo[bien["bien_id"]] = momento

    def devolver(self, receptor, movimiento_id, momento, bienes):
        self.pedir(
            receptor,
            "POST",
            f"/movimientos/{movimiento_id}/recepcion",
            {
                "resultado": "DEVUELTO",
                "motivo": self.azar.choice(MOTIVOS_DEVOLUCION),
                "bienes_con_novedad": [bienes[0]["bien_id"]],
            },
        )
        self.fechar_ultimo("recepcion", "movimiento_id", movimiento_id, momento)

    def desistir(self, origen, movimiento_id, momento):
        self.pedir(
            origen,
            "POST",
            f"/movimientos/{movimiento_id}/desistimiento",
            {"motivo": "Se desiste de la entrega, los bienes quedan en la unidad"},
        )
        self.fechar_ultimo("recepcion", "movimiento_id", movimiento_id, momento)

    def corregir_devuelta(self, origen, destino, movimiento_id, momento, bienes, tipos):
        acta = self.pedir(origen, "GET", f"/movimientos/{movimiento_id}")
        ids = [bien["bien_id"] for bien in bienes]
        reemplazo = [
            b
            for b in self.elegir_h(origen, [bienes[0]["tipo_bien"]], 3, momento)
            if b["bien_id"] not in ids
        ]
        if reemplazo:
            ids[0] = reemplazo[0]["bien_id"]
        self.pedir(
            origen,
            "PUT",
            f"/movimientos/{movimiento_id}",
            {
                "numero_acta": acta["numero_acta"],
                "fecha_hecho": acta["fecha_hecho"],
                "descripcion": acta["descripcion"],
                "bienes": ids,
                "unidad_destino_id": self.unidad_id[destino],
            },
        )
        self.fechar_ultimo("rectificacion", "movimiento_id", movimiento_id, momento)
        return [{"bien_id": i, "tipo_bien": bienes[0]["tipo_bien"]} for i in ids]

    def revisar_acta(self, regional, movimiento_id, momento, observacion=None):
        acta = self.pedir(regional, "GET", f"/movimientos/{movimiento_id}")
        cuerpo = {"resultado": "REVISADO", "version": acta["version_vigente"]}
        if observacion:
            cuerpo = {
                **cuerpo,
                "resultado": "OBSERVADO",
                "motivo_observacion": observacion,
            }
        self.pedir(regional, "POST", f"/movimientos/{movimiento_id}/revisiones", cuerpo)
        self.fechar_ultimo("revision", "movimiento_id", movimiento_id, momento)

    def rectificar_acta(self, origen, movimiento_id, clase, momento):
        acta = self.pedir(origen, "GET", f"/movimientos/{movimiento_id}")
        fecha, numero, descripcion = (
            acta["fecha_hecho"],
            acta["numero_acta"],
            acta["descripcion"],
        )
        if clase == "fecha":
            corregida = datetime.fromisoformat(fecha) - timedelta(days=2)
            fecha = corregida.date().isoformat()
        elif clase == "descripcion":
            descripcion = (
                descripcion or ""
            ) + ". Ver detalle de bienes en el acta firmada"
        self.pedir(
            origen,
            "POST",
            f"/movimientos/{movimiento_id}/rectificaciones",
            {
                "fecha_hecho": fecha,
                "numero_acta": numero,
                "descripcion": descripcion,
                "motivo": OBSERVACIONES[clase][1],
            },
        )
        self.fechar_ultimo("rectificacion", "movimiento_id", movimiento_id, momento)

    def revisiones_de(self, origen, movimiento_id, inicio, final, clases, rapido):
        """Las revisiones de un acta aplicada, según cómo termina."""
        regional = SUPERIOR[origen]
        minimo, maximo = (1, 1) if rapido else (2, 5)
        momento = self.despues(inicio, minimo, maximo)
        if final == "revisada":
            self.revisar_acta(regional, movimiento_id, momento)
            return
        for clase in clases or ["fecha"]:
            self.revisar_acta(regional, movimiento_id, momento, OBSERVACIONES[clase][0])
            if final == "observada":
                return
            momento = self.despues(momento, 1, 3)
            self.rectificar_acta(origen, movimiento_id, clase, momento)
            momento = self.despues(momento, 1, 3)
        self.revisar_acta(regional, movimiento_id, momento)

    @seguro
    def ciclo(
        self, origen, destino, tipos, cantidad, inicio, final="revisada", clases=None
    ):
        """Una entrega y todo lo que le pasa. `final` dice en qué estado queda."""
        etiqueta = f"{inicio:%d/%m} {origen}->{destino} {final}"
        bienes = self.elegir_h(origen, tipos, cantidad, inicio)
        if not bienes:
            print(f"  -- {etiqueta}: sin bienes de {tipos}, se omite")
            return
        rapido = inicio.month == 11
        movimiento_id = self.crear_entrega(origen, destino, bienes, inicio, tipos)
        for bien in bienes:
            self.ultimo[bien["bien_id"]] = inicio
        if final == "pendiente":
            print(f"  ok {etiqueta} (acta {movimiento_id})")
            return
        momento = self.despues(inicio, 1, 1 if rapido else 2)
        if final in ("devuelta", "devuelta_corregida", "rechazada"):
            self.devolver(destino, movimiento_id, momento, bienes)
            if final == "devuelta":
                print(f"  ok {etiqueta} (acta {movimiento_id})")
                return
            momento = self.despues(momento, 1, 3)
            if final == "rechazada":
                self.desistir(origen, movimiento_id, momento)
                print(f"  ok {etiqueta} (acta {movimiento_id})")
                return
            bienes = self.corregir_devuelta(
                origen, destino, movimiento_id, momento, bienes, tipos
            )
            momento = self.despues(momento, 1, 2)
        self.aceptar(destino, movimiento_id, momento, bienes)
        if origen != "direccion" and final != "sin_revisar":
            resultado = "observada" if final == "observada" else "revisada"
            if final.startswith("obs_rect"):
                resultado = "obs_rect"
            self.revisiones_de(
                origen, movimiento_id, momento, resultado, clases, rapido
            )
        print(f"  ok {etiqueta} (acta {movimiento_id})")

    # ---- dotaciones y devoluciones de oficiales -----------------------------

    @seguro
    def dotacion(self, unidad, tipos, inicio, final="revisada"):
        etiqueta = f"{inicio:%d/%m} dotación en {unidad}"
        bienes = self.elegir_h(unidad, tipos, 1, inicio)
        if not bienes:
            print(f"  -- {etiqueta}: sin bienes, se omite")
            return
        for oficial in self.pedir(unidad, "GET", "/oficiales"):
            codigo, acta = llamar(
                "POST",
                "/movimientos/dotaciones",
                self.tokens[unidad],
                {
                    "numero_acta": self.numero_de_prueba(),
                    "fecha_hecho": inicio.date().isoformat(),
                    "descripcion": f"Asignación de {bienes[0]['marca']} {bienes[0]['modelo']} al oficial {oficial['nombre']}",
                    "bienes": [bienes[0]["bien_id"]],
                    "oficial_id": oficial["id"],
                },
                esperado=(201, 409),
            )
            if codigo == 201:
                self.fechar_movimiento(acta["id"], inicio)
                self.ultimo[bienes[0]["bien_id"]] = inicio
                if unidad != "direccion" and final == "revisada":
                    self.revisar_acta(
                        SUPERIOR[unidad], acta["id"], self.despues(inicio, 2, 5)
                    )
                print(f"  ok {etiqueta} (acta {acta['id']})")
                return
        print(f"  -- {etiqueta}: ningún oficial podía recibirlo")

    @seguro
    def devolucion(self, unidad, inicio, final="revisada"):
        etiqueta = f"{inicio:%d/%m} devolución de un oficial de {unidad}"
        oficiales = {o["legajo"]: o for o in self.pedir(unidad, "GET", "/oficiales")}
        candidatos = [
            b
            for b in self.elegir_h(unidad, ARM, 50, inicio, "DOTACION")
            if b["oficial_legajo"] in oficiales
        ]
        if not candidatos:
            print(f"  -- {etiqueta}: sin armas en dotación, se omite")
            return
        bien = candidatos[0]
        oficial = oficiales[bien["oficial_legajo"]]
        sala = self.ubicaciones(unidad)["Sala de Armas"]
        acta = self.pedir(
            unidad,
            "POST",
            "/movimientos/devoluciones",
            {
                "numero_acta": self.numero_de_prueba(),
                "fecha_hecho": inicio.date().isoformat(),
                "descripcion": f"Devolución del arma del oficial {oficial['nombre']}",
                "oficial_id": oficial["id"],
                "ubicaciones": [{"bien_id": bien["bien_id"], "ubicacion_id": sala}],
            },
        )
        self.fechar_movimiento(acta["id"], inicio)
        self.ultimo[bien["bien_id"]] = inicio
        if unidad != "direccion" and final == "revisada":
            self.revisar_acta(SUPERIOR[unidad], acta["id"], self.despues(inicio, 2, 5))
        print(f"  ok {etiqueta} (acta {acta['id']})")

    # ---- cambios de estado de servicio --------------------------------------

    def informe(self, unidad, bien, momento, diagnostico):
        self.informes += 1
        return crear_pdf(
            [
                "INFORME TÉCNICO",
                f"N° {self.informes:03d}/2026 - {NOMBRE_UNIDAD[unidad]}",
                f"Fecha: {momento:%d/%m/%Y}",
                "",
                f"Bien: {bien['tipo_bien']} {bien['marca']} {bien['modelo']}",
                f"Identificación: {bien['identificacion']}",
                "",
                "Diagnóstico:",
                diagnostico,
                "",
                "Firma del técnico: ______________________",
            ]
        )

    def registrar_cambio(self, unidad, bien, nuevo, observacion, momento, con_informe):
        campos = {"estado_nuevo": nuevo, "observaciones": observacion}
        archivo = None
        if con_informe:
            nombre = f"informe_{bien['identificacion']}_{momento:%Y%m%d}.pdf".replace(
                " ", "_"
            ).replace("/", "-")
            archivo = (
                "informe",
                nombre,
                self.informe(unidad, bien, momento, observacion),
            )
        cuerpo, tipo = multipart(campos, archivo)
        cambio = enviar(
            "POST",
            f"/bienes/{bien['bien_id']}/cambios-estado",
            self.tokens[unidad],
            cuerpo,
            tipo,
        )
        self.ejecutar(
            "UPDATE cambio_estado_operativo SET fecha = :t WHERE id = :id",
            t=momento,
            id=cambio["id"],
        )
        self.ejecutar(
            "UPDATE documento SET fecha_carga = :t WHERE id ="
            " (SELECT documento_id FROM cambio_estado_operativo WHERE id = :id)",
            t=momento,
            id=cambio["id"],
        )
        self.ultimo[bien["bien_id"]] = momento
        return cambio["id"]

    def revisar_cambio(self, regional, cambio_id, momento, observacion=None):
        cambio = self.pedir(regional, "GET", f"/cambios-estado/{cambio_id}")
        cuerpo = {"resultado": "REVISADO", "version": cambio["version_vigente"]}
        if observacion:
            cuerpo = {
                **cuerpo,
                "resultado": "OBSERVADO",
                "motivo_observacion": observacion,
            }
        self.pedir(regional, "POST", f"/cambios-estado/{cambio_id}/revisiones", cuerpo)
        self.fechar_ultimo("revision", "cambio_estado_id", cambio_id, momento)

    def rectificar_cambio(self, unidad, cambio_id, momento):
        cambio = self.pedir(unidad, "GET", f"/cambios-estado/{cambio_id}")
        cuerpo, tipo = multipart(
            {
                "version": cambio["version_vigente"],
                "observaciones": cambio["observaciones"]
                + ". Causa confirmada por el taller",
                "motivo": "Se completó la observación con la causa confirmada por el taller",
                "quitar_informe": "false",
            }
        )
        enviar(
            "POST",
            f"/cambios-estado/{cambio_id}/rectificaciones",
            self.tokens[unidad],
            cuerpo,
            tipo,
        )
        self.fechar_ultimo(
            "rectificacion_cambio_estado", "cambio_estado_id", cambio_id, momento
        )

    def revisiones_de_cambio(self, unidad, cambio_id, inicio, final, rapido):
        if unidad == "direccion" or final == "sin_revisar":
            return
        regional = SUPERIOR[unidad]
        momento = self.despues(inicio, 1 if rapido else 2, 1 if rapido else 5)
        if final == "revisada":
            self.revisar_cambio(regional, cambio_id, momento)
            return
        self.revisar_cambio(
            regional,
            cambio_id,
            momento,
            "El informe técnico no detalla la causa de la falla",
        )
        if final == "observada":
            return
        momento = self.despues(momento, 1, 3)
        self.rectificar_cambio(unidad, cambio_id, momento)
        self.revisar_cambio(regional, cambio_id, self.despues(momento, 1, 3))

    @seguro
    def cambio(self, unidad, tipos, tenencia, inicio, final="revisada", vuelve=None):
        etiqueta = f"{inicio:%d/%m} cambio de estado en {unidad} ({tipos[0]}) {final}"
        bienes = self.elegir_h(unidad, tipos, 1, inicio, tenencia)
        if not bienes:
            print(f"  -- {etiqueta}: sin bienes, se omite")
            return
        bien = bienes[0]
        falla, arreglo = FALLAS[bien["tipo_bien"]]
        rapido = inicio.month == 11
        cambio_id = self.registrar_cambio(
            unidad, bien, "FUERA_DE_SERVICIO", falla, inicio, True
        )
        self.revisiones_de_cambio(unidad, cambio_id, inicio, final, rapido)
        if vuelve:
            regreso = self.despues(inicio, *vuelve)
            vuelta_id = self.registrar_cambio(
                unidad, bien, "EN_SERVICIO", arreglo, regreso, False
            )
            self.revisiones_de_cambio(unidad, vuelta_id, regreso, "revisada", False)
        print(f"  ok {etiqueta} (cambio {cambio_id})")

    # ---- la historia --------------------------------------------------------

    def historia(self):
        T = self.T
        print("Julio")
        self.ciclo("direccion", "norte", ARM, 1, T(7, 6))
        self.ciclo("direccion", "sur", ARM, 1, T(7, 8))
        self.ciclo("direccion", "norte", CHA, 3, T(7, 13))
        self.ciclo("direccion", "sur", CHA, 2, T(7, 15))
        self.ciclo("norte", "a", AREA_SEGURIDAD, 2, T(7, 20))
        self.ciclo("sur", "c", AREA_SEGURIDAD, 2, T(7, 22))
        self.ciclo("norte", "b", CHA, 2, T(7, 27), "obs_rect", ["fecha"])
        print("Agosto")
        self.ciclo("a", "b", EQP, 2, T(8, 3))
        self.ciclo("direccion", "norte", MOV, 1, T(8, 5))
        self.ciclo("norte", "a", MOV, 1, T(8, 10))
        self.ciclo("c", "a", CHA, 1, T(8, 12), "devuelta_corregida")
        self.ciclo("b", "c", EQP, 1, T(8, 17), "obs_rect2", ["fecha", "descripcion"])
        self.dotacion("a", ARM, T(8, 19))
        self.devolucion("b", T(8, 24))
        self.cambio("a", MOV, "DEPOSITO", T(8, 26), "revisada", vuelve=(14, 20))
        self.ciclo("sur", "c", MOV, 1, T(8, 31))
        print("Septiembre")
        self.ciclo("a", "b", ARM, 1, T(9, 2))
        self.ciclo("b", "a", CHA, 1, T(9, 7), "obs_rect", ["numero"])
        self.ciclo("c", "b", ARM, 1, T(9, 9), "rechazada")
        self.cambio("b", ARM, "DEPOSITO", T(9, 11))
        self.ciclo("direccion", "sur", EQP, 2, T(9, 15))
        self.ciclo("sur", "c", EQP, 1, T(9, 21))
        self.dotacion("c", ARM, T(9, 23))
        self.cambio("c", EQP, "DOTACION", T(9, 28), "obs_rect", vuelve=(15, 25))
        print("Octubre")
        self.ciclo("norte", "b", ARM, 1, T(10, 1))
        self.devolucion("a", T(10, 5))
        self.cambio("norte", MOV, "DEPOSITO", T(10, 7))
        self.ciclo("a", "c", AREA_SEGURIDAD, 1, T(10, 13))
        self.cambio("a", CHA, "DOTACION", T(10, 15))
        self.ciclo("direccion", "a", EQP, 1, T(10, 16))
        self.ciclo("b", "norte", EQP, 1, T(10, 19))
        self.dotacion("b", EQP, T(10, 22))
        self.cambio("c", CHA, "DOTACION", T(10, 24))
        print("Noviembre: lo que está en curso")
        self.ciclo("norte", "a", EQP, 1, T(11, 1), "observada", ["descripcion"])
        self.ciclo("norte", "b", CHA, 1, T(11, 2), "devuelta")
        self.cambio("c", MOV, "DEPOSITO", T(11, 3), "observada")
        self.ciclo("b", "a", EQP, 1, T(11, 3), "observada", ["fecha"])
        self.ciclo("a", "c", EQP, 1, T(11, 4), "devuelta")
        self.ciclo("c", "a", MOV, 1, T(11, 4), "devuelta")
        self.ciclo("sur", "c", CHA, 1, T(11, 5), "devuelta")
        self.ciclo("a", "b", MOV, 1, T(11, 5), "sin_revisar")
        self.cambio("a", EQP, "DOTACION", T(11, 5), "observada")
        self.ciclo("norte", "a", MOV, 1, T(11, 6), "sin_revisar")
        self.ciclo("direccion", "norte", EQP, 1, T(11, 6), "pendiente")
        self.ciclo("sur", "c", EQP, 1, T(11, 6), "sin_revisar")
        self.cambio("sur", MOV, "DEPOSITO", T(11, 7), "sin_revisar")
        self.ciclo("direccion", "sur", CHA, 1, T(11, 7), "pendiente")
        self.cambio("b", EQP, "DEPOSITO", T(11, 8), "sin_revisar")
        self.ciclo("sur", "direccion", EQP, 1, T(11, 8), "pendiente")
        self.ciclo("sur", "c", ARM, 1, T(11, 8), "pendiente")
        self.ciclo("direccion", "a", ARM, 1, T(11, 9), "pendiente")

    def complemento(self):
        """Dotaciones que `historia` omitió porque todos los oficiales ya tenían un arma."""
        T = self.T
        self.dotacion("a", EQP, T(8, 19))
        self.dotacion("c", EQP, T(9, 23))
        self.dotacion("a", ARM, T(10, 9))
        self.devolucion("c", T(10, 12))
        self.dotacion("c", ARM, T(10, 14))
        self.dotacion("b", ARM, T(10, 27))
        # Lo que la Operacional C dejó para revisar de la Regional Sur.
        self.ciclo("c", "b", EQP, 1, T(11, 7), "sin_revisar")
        self.cambio("c", ARM, "DEPOSITO", T(11, 8), "sin_revisar")

    # ---- cierre: fechas de lo existente, numeración, actas escaneadas ---------

    def fechar_existentes(self):
        """Lleva a fechas coherentes lo que cargó cargar_demo.py (movimientos 1 a 16)."""
        for movimiento_id, hecho in self.consultar(
            "SELECT id, fecha_hecho FROM movimiento WHERE id <= 16 ORDER BY id"
        ):
            carga = datetime(
                hecho.year,
                hecho.month,
                hecho.day,
                self.azar.randint(9, 14),
                self.azar.randint(0, 59),
            )
            carga = self.tope(carga)
            self.fechar_movimiento(movimiento_id, carga)
            momento = carga
            for (fila,) in self.consultar(
                "SELECT id FROM recepcion WHERE movimiento_id = :i ORDER BY id",
                i=movimiento_id,
            ):
                momento = self.despues(momento, 1, 1)
                self.ejecutar(
                    "UPDATE recepcion SET fecha = :t WHERE id = :i", t=momento, i=fila
                )
            revisiones = self.consultar(
                "SELECT id FROM revision WHERE movimiento_id = :i ORDER BY id",
                i=movimiento_id,
            )
            rectificaciones = self.consultar(
                "SELECT id FROM rectificacion WHERE movimiento_id = :i ORDER BY id",
                i=movimiento_id,
            )
            for posicion, (fila,) in enumerate(revisiones):
                momento = self.despues(momento, 1, 2)
                self.ejecutar(
                    "UPDATE revision SET fecha = :t WHERE id = :i", t=momento, i=fila
                )
                if posicion < len(rectificaciones):
                    momento = self.despues(momento, 1, 1)
                    self.ejecutar(
                        "UPDATE rectificacion SET fecha = :t WHERE id = :i",
                        t=momento,
                        i=rectificaciones[posicion][0],
                    )

    def numeros_correctos(self):
        """Número de acta de cada movimiento: cada unidad numera los suyos en orden cronológico."""
        correctos = {}
        for clave, unidad_id in self.unidad_id.items():
            filas = self.consultar(
                "SELECT id FROM movimiento WHERE unidad_registrante_id = :u ORDER BY fecha_carga, id",
                u=unidad_id,
            )
            for posicion, (movimiento_id,) in enumerate(filas):
                correctos[movimiento_id] = (
                    clave,
                    f"{NUMERO_INICIAL[clave] + posicion:04d}/2026",
                )
        return correctos

    def renumerar(self):
        con_error = {
            fila[0]
            for fila in self.consultar(
                "SELECT DISTINCT movimiento_id FROM revision WHERE resultado = 'OBSERVADO'"
                " AND movimiento_id IS NOT NULL AND motivo_observacion LIKE '%número de acta%'"
            )
        }
        for movimiento_id, (_, correcto) in self.numeros_correctos().items():
            digitos = correcto[:4]
            con_tipeo = digitos[:2] + digitos[3] + digitos[2]
            if con_tipeo == digitos:
                con_tipeo = f"{int(digitos) + 1:04d}"
            vigente = f"{con_tipeo}/2026" if movimiento_id in con_error else correcto
            self.ejecutar(
                "UPDATE movimiento SET numero_acta = :n WHERE id = :i",
                n=vigente,
                i=movimiento_id,
            )
            self.ejecutar(
                "UPDATE rectificacion SET numero_acta = :n WHERE movimiento_id = :i",
                n=correcto,
                i=movimiento_id,
            )

    def adjuntar_actas(self):
        correctos = self.numeros_correctos()
        for movimiento_id, (clave, correcto) in sorted(correctos.items()):
            if self.consultar(
                "SELECT 1 FROM movimiento_documento WHERE movimiento_id = :i",
                i=movimiento_id,
            ):
                continue
            acta = self.pedir(clave, "GET", f"/movimientos/{movimiento_id}")
            if acta["tipo"] == "BAJA":
                titulo = "ACTA DE BAJA DE BIENES"
            elif acta["oficial_destino"]:
                titulo = "ACTA DE ASIGNACIÓN EN DOTACIÓN"
            elif acta["oficial_origen"]:
                titulo = "ACTA DE DEVOLUCIÓN DE OFICIAL"
            else:
                titulo = "ACTA DE ENTREGA DE BIENES"
            fecha = datetime.fromisoformat(acta["fecha_hecho"])
            origen = acta["unidad_origen"]["nombre"] if acta["unidad_origen"] else "-"
            if acta["oficial_origen"]:
                oficial = acta["oficial_origen"]
                origen += f" (oficial {oficial['nombre']}, legajo {oficial['legajo']})"
            destino = (
                acta["unidad_destino"]["nombre"] if acta["unidad_destino"] else "Baja"
            )
            if acta["oficial_destino"]:
                oficial = acta["oficial_destino"]
                destino = f"{acta['unidad_origen']['nombre']} (oficial {oficial['nombre']}, legajo {oficial['legajo']})"
            lineas = [
                "Dirección Logística",
                titulo,
                f"Acta N° {correcto}",
                f"Fecha del hecho: {fecha:%d/%m/%Y}",
                "",
                f"Origen: {origen}",
                f"Destino: {destino}",
                "",
                "Bienes:",
            ]
            lineas += [
                f"- {r['tipo_bien']} {r['marca']} {r['modelo']} - {r['identificacion']}"
                for r in acta["bienes"]
            ]
            lineas += [
                "",
                f"Descripción: {acta['descripcion'] or '-'}",
                "",
                "Firma del responsable: ______________________",
            ]
            nombre = f"acta_{correcto.replace('/', '-')}_{clave}.pdf"
            cuerpo, tipo = multipart({}, ("archivo", nombre, crear_pdf(lineas)))
            documento = enviar(
                "POST",
                f"/movimientos/{movimiento_id}/documentos",
                self.tokens[clave],
                cuerpo,
                tipo,
            )
            carga = self.consultar(
                "SELECT fecha_carga FROM movimiento WHERE id = :i", i=movimiento_id
            )[0][0]
            momento = self.tope(carga + timedelta(minutes=self.azar.randint(10, 120)))
            self.ejecutar(
                "UPDATE documento SET fecha_carga = :t WHERE id = :i",
                t=momento,
                i=documento["id"],
            )
        print(
            f"  documentos cargados: {self.consultar('SELECT COUNT(*) FROM documento')[0][0]}"
        )

    def resumen(self):
        print("\nLo que ve cada usuario:")
        print(
            f"{'usuario':26} por recibir | devueltas | observados (acta/cambio) | para revisar"
        )
        for clave, nombre in USUARIOS.items():
            recibir = len(self.pedir(clave, "GET", "/movimientos/por-recibir"))
            devueltas = len(self.pedir(clave, "GET", "/movimientos/devueltas"))
            obs_actas = len(self.pedir(clave, "GET", "/movimientos/observados"))
            obs_cambios = len(self.pedir(clave, "GET", "/cambios-estado/observados"))
            revisar = len(self.pedir(clave, "GET", "/revisiones/bandeja"))
            print(
                f"{nombre:26} {recibir:10} | {devueltas:9} | {obs_actas:9} / {obs_cambios:<12} | {revisar}"
            )
        print("\nMovimientos por estado:")
        for fila in self.consultar(
            "SELECT estado, estado_revision, COUNT(*) FROM movimiento GROUP BY 1, 2 ORDER BY 1, 2"
        ):
            print(f"  {fila[0]:10} {fila[1]:10} {fila[2]}")
        cambios = self.consultar("SELECT COUNT(*) FROM cambio_estado_operativo")[0][0]
        fuera = self.consultar(
            "SELECT COUNT(*) FROM bien WHERE estado_operativo = 'FUERA_DE_SERVICIO'"
        )[0][0]
        print(f"\nCambios de estado: {cambios}. Bienes hoy fuera de servicio: {fuera}.")

    def coherencia(self):
        print("\nChequeos de coherencia (todos tienen que dar 0):")
        chequeos = {
            "movimientos con fecha futura o hecho posterior a la carga": (
                "SELECT COUNT(*) FROM movimiento WHERE fecha_carga > NOW() OR fecha_hecho > DATE(fecha_carga)"
            ),
            "recepciones antes de la carga del acta": (
                "SELECT COUNT(*) FROM recepcion r JOIN movimiento m ON m.id = r.movimiento_id"
                " WHERE r.fecha < m.fecha_carga"
            ),
            "revisiones de actas antes de que se apliquen": (
                "SELECT COUNT(*) FROM revision v JOIN movimiento m ON m.id = v.movimiento_id"
                " WHERE v.fecha < COALESCE((SELECT MAX(r.fecha) FROM recepcion r WHERE r.movimiento_id = m.id"
                " AND r.resultado = 'ACEPTADO'), m.fecha_carga)"
            ),
            "revisiones de cambios antes del cambio": (
                "SELECT COUNT(*) FROM revision v JOIN cambio_estado_operativo c ON c.id = v.cambio_estado_id"
                " WHERE v.fecha < c.fecha"
            ),
            "rectificaciones antes de la carga": (
                "SELECT COUNT(*) FROM rectificacion x JOIN movimiento m ON m.id = x.movimiento_id"
                " WHERE x.fecha < m.fecha_carga"
            ),
            "documentos cargados antes del acta": (
                "SELECT COUNT(*) FROM movimiento_documento md JOIN movimiento m ON m.id = md.movimiento_id"
                " JOIN documento d ON d.id = md.documento_id WHERE d.fecha_carga < m.fecha_carga"
            ),
            "actas fechadas antes de que existiera el usuario": (
                "SELECT COUNT(*) FROM movimiento m JOIN usuario u ON u.id = m.usuario_id"
                " WHERE m.fecha_carga < u.fecha_alta"
            ),
        }
        for nombre, sentencia in chequeos.items():
            print(f"  {self.consultar(sentencia)[0][0]}  {nombre}")
        filas = self.consultar(
            "SELECT bien_id, orden, f FROM ("
            " SELECT mb.bien_id, mb.orden, COALESCE((SELECT MAX(r.fecha) FROM recepcion r"
            "   WHERE r.movimiento_id = m.id AND r.resultado = 'ACEPTADO'), m.fecha_carga) f"
            " FROM movimiento_bien mb JOIN movimiento m ON m.id = mb.movimiento_id"
            " WHERE m.estado = 'APLICADO' AND mb.orden IS NOT NULL"
            " UNION ALL SELECT bien_id, orden, fecha FROM cambio_estado_operativo"
            ") t ORDER BY bien_id, orden"
        )
        fuera_de_orden, anterior = 0, {}
        for bien_id, _, momento in filas:
            if bien_id in anterior and momento < anterior[bien_id]:
                fuera_de_orden += 1
            anterior[bien_id] = momento
        print(
            f"  {fuera_de_orden}  bienes con movimientos o cambios fuera del orden de aplicación"
        )

    def cerrar(self):
        print("Fechas de lo que ya estaba cargado")
        self.ejecutar("UPDATE usuario SET fecha_alta = '2026-06-15 09:00:00'")
        self.fechar_existentes()
        print("Numeración de actas por unidad")
        self.renumerar()
        print("Actas escaneadas")
        self.adjuntar_actas()
        self.resumen()
        self.coherencia()


def main():
    comando = (sys.argv[1:] or [""])[0]
    if comando == "historia":
        historia = Historia()
        existe = llamar(
            "GET",
            "/movimientos/17",
            historia.tokens["direccion"],
            esperado=(200, 403, 404),
        )[0]
        if existe == 200:
            print("La historia ya está cargada, no se cargó nada.")
            return 0
        historia.historia()
        print("Historia cargada. Falta correr `cerrar`.")
        return 0
    if comando == "complemento":
        Historia().complemento()
        return 0
    if comando == "cerrar":
        Historia().cerrar()
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
