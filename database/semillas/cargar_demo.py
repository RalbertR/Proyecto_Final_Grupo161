"""Carga actas de demostración recorriendo la API, para tener todos los estados.

Se corre después de cargar_datos_prueba.py, con el backend levantado:

    docker compose run --rm semillas python /semillas/cargar_demo.py

Usa solo la biblioteca estándar. Pasa por la API y no por SQL, así que cada acta
respeta las reglas y los triggers. Lo que deja en cada estado:

- pendientes de recepción, devuelta al origen y rechazada (el origen desiste);
- aplicadas, sin revisar, revisadas y observadas;
- una rectificada y revisada;
- dotaciones y una devolución de un oficial;
- una entrega de Dirección, que no se revisa.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from typing import Any

BASE = os.environ.get("API_URL", "http://backend:8000/api").rstrip("/")
CONTRASENA = os.environ["CONTRASENA_DEMO"]

USUARIOS = {
    "direccion": "logistico.direccion",
    "norte": "logistico.regional_norte",
    "sur": "logistico.regional_sur",
    "a": "aux.unidad_a",
    "b": "aux.unidad_b",
    "c": "aux.unidad_c",
}
ARMAMENTO = ["ARMAMENTO"]
CHALECOS = ["CHALECO"]
MOVILES = ["MOVIL"]
EQUIPOS = ["EQUIPO_COMUNICACIONES"]
UBICACION_POR_TIPO = {
    "ARMAMENTO": "Sala de Armas",
    "CHALECO": "Sala de Armas",
    "EQUIPO_COMUNICACIONES": "Depósito",
    "MOVIL": "Playón",
}


class Fallo(Exception):
    pass


def llamar(
    metodo, ruta, token=None, cuerpo=None, formulario=None, esperado=(200, 201)
) -> tuple[int, Any]:
    datos = None
    cabeceras = {}
    if formulario is not None:
        datos = urllib.parse.urlencode(formulario).encode()
        cabeceras["Content-Type"] = "application/x-www-form-urlencoded"
    elif cuerpo is not None:
        datos = json.dumps(cuerpo).encode()
        cabeceras["Content-Type"] = "application/json"
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    pedido = urllib.request.Request(
        BASE + ruta, data=datos, headers=cabeceras, method=metodo
    )
    try:
        with urllib.request.urlopen(pedido) as respuesta:
            codigo, texto = respuesta.status, respuesta.read()
    except urllib.error.HTTPError as error:
        codigo, texto = error.code, error.read()
    cuerpo_json = json.loads(texto) if texto else None
    if codigo not in esperado:
        raise Fallo(f"{metodo} {ruta} respondió {codigo}: {cuerpo_json}")
    return codigo, cuerpo_json


class Demo:
    def __init__(self):
        self.tokens = {}
        self.unidad_id = {}
        self.hoy = date.today()
        for clave, nombre in USUARIOS.items():
            _, sesion = llamar(
                "POST",
                "/auth/login",
                formulario={"username": nombre, "password": CONTRASENA},
            )
            self.tokens[clave] = sesion["access_token"]
            _, yo = llamar("GET", "/auth/me", self.tokens[clave])
            self.unidad_id[clave] = yo["unidad"]["id"]

    def pedir(self, quien, metodo, ruta, cuerpo=None, esperado=(200, 201)):
        return llamar(metodo, ruta, self.tokens[quien], cuerpo, esperado=esperado)[1]

    def fecha(self, dias_atras):
        return (self.hoy - timedelta(days=dias_atras)).isoformat()

    def elegir(self, quien, tipos, cantidad, tenencia="DEPOSITO", oficial=None):
        inventario = self.pedir(quien, "GET", "/inventario")
        propios = [
            bien
            for bien in inventario
            if bien["unidad_id"] == self.unidad_id[quien]
            and bien["tipo_bien"] in tipos
            and bien["tenencia"] == tenencia
            and bien["estado_operativo"] == "EN_SERVICIO"
            and not bien["con_movimiento_pendiente"]
            and (oficial is None or bien["oficial_legajo"] == oficial)
        ]
        return [bien["bien_id"] for bien in propios[:cantidad]]

    def entregar(self, origen, destino, tipos, cantidad, acta, descripcion, dias):
        bienes = self.elegir(origen, tipos, cantidad)
        if not bienes:
            print(f"  (sin bienes de {tipos} en {origen}; se omite el acta {acta})")
            return None
        acta_creada = self.pedir(
            origen,
            "POST",
            "/movimientos/entregas",
            {
                "numero_acta": acta,
                "fecha_hecho": self.fecha(dias),
                "descripcion": descripcion,
                "bienes": bienes,
                "unidad_destino_id": self.unidad_id[destino],
            },
        )
        print(f"  acta {acta}: {origen} -> {destino}, pendiente de recepción")
        return acta_creada["id"]

    def ubicaciones(self, quien):
        lista = self.pedir(quien, "GET", "/ubicaciones")
        return {ubicacion["nombre"]: ubicacion["id"] for ubicacion in lista}

    def aceptar(self, receptor, movimiento_id):
        acta = self.pedir(receptor, "GET", f"/movimientos/{movimiento_id}")
        propias = self.ubicaciones(receptor)
        self.pedir(
            receptor,
            "POST",
            f"/movimientos/{movimiento_id}/recepcion",
            {
                "resultado": "ACEPTADO",
                "ubicaciones": [
                    {
                        "bien_id": renglon["bien_id"],
                        "ubicacion_id": propias[
                            UBICACION_POR_TIPO[renglon["tipo_bien"]]
                        ],
                    }
                    for renglon in acta["bienes"]
                ],
            },
        )
        print(f"    recibida por {receptor}")

    def devolver_al_origen(self, receptor, movimiento_id, motivo):
        acta = self.pedir(receptor, "GET", f"/movimientos/{movimiento_id}")
        self.pedir(
            receptor,
            "POST",
            f"/movimientos/{movimiento_id}/recepcion",
            {
                "resultado": "DEVUELTO",
                "motivo": motivo,
                "bienes_con_novedad": [acta["bienes"][0]["bien_id"]],
            },
        )
        print(f"    devuelta al origen por {receptor}")

    def revisar(self, regional, movimiento_id, observacion=None):
        acta = self.pedir(regional, "GET", f"/movimientos/{movimiento_id}")
        cuerpo = {"resultado": "REVISADO", "version": acta["version_vigente"]}
        if observacion:
            cuerpo = {
                "resultado": "OBSERVADO",
                "version": acta["version_vigente"],
                "motivo_observacion": observacion,
            }
        self.pedir(regional, "POST", f"/movimientos/{movimiento_id}/revisiones", cuerpo)
        print(f"    {cuerpo['resultado'].lower()} por {regional}")

    def rectificar(self, autor, movimiento_id, motivo, descripcion, dias):
        acta = self.pedir(autor, "GET", f"/movimientos/{movimiento_id}")
        self.pedir(
            autor,
            "POST",
            f"/movimientos/{movimiento_id}/rectificaciones",
            {
                "numero_acta": acta["numero_acta"],
                "fecha_hecho": self.fecha(dias),
                "descripcion": descripcion,
                "motivo": motivo,
            },
        )
        print(f"    rectificada por {autor}")

    def oficial_con_bienes(self, quien):
        """Un oficial de la unidad con un arma en dotación: (id, legajo)."""
        oficiales = {
            o["legajo"]: o["id"] for o in self.pedir(quien, "GET", "/oficiales")
        }
        for bien in self.pedir(quien, "GET", "/inventario"):
            legajo = bien["oficial_legajo"]
            if (
                bien["unidad_id"] == self.unidad_id[quien]
                and bien["tenencia"] == "DOTACION"
                and bien["tipo_bien"] == "ARMAMENTO"
                and not bien["con_movimiento_pendiente"]
                and legajo in oficiales
            ):
                return oficiales[legajo], legajo
        return None, None

    def dotar(self, quien, tipos, acta, descripcion, dias, oficial_id=None):
        bienes = self.elegir(quien, tipos, 1)
        if not bienes:
            print(f"  (sin bienes de {tipos} en depósito en {quien}; se omite {acta})")
            return None
        if oficial_id:
            candidatos = [oficial_id]
        else:
            candidatos = [o["id"] for o in self.pedir(quien, "GET", "/oficiales")]
        for candidato in candidatos:
            codigo, creada = llamar(
                "POST",
                "/movimientos/dotaciones",
                self.tokens[quien],
                {
                    "numero_acta": acta,
                    "fecha_hecho": self.fecha(dias),
                    "descripcion": descripcion,
                    "bienes": bienes,
                    "oficial_id": candidato,
                },
                esperado=(201, 409),
            )
            if codigo == 201:
                print(f"  acta {acta}: dotación en {quien}, aplicada")
                return creada["id"]
        print(f"  (ningún oficial de {quien} podía recibir {tipos}; se omite {acta})")
        return None

    def devolucion_de_oficial(self, quien, acta, descripcion, dias):
        oficial_id, legajo = self.oficial_con_bienes(quien)
        bienes = self.elegir(quien, ARMAMENTO, 1, "DOTACION", legajo) if legajo else []
        if not bienes:
            print(f"  (sin armamento en dotación en {quien}; se omite {acta})")
            return None, None
        sala = self.ubicaciones(quien)["Sala de Armas"]
        creada = self.pedir(
            quien,
            "POST",
            "/movimientos/devoluciones",
            {
                "numero_acta": acta,
                "fecha_hecho": self.fecha(dias),
                "descripcion": descripcion,
                "oficial_id": oficial_id,
                "ubicaciones": [{"bien_id": b, "ubicacion_id": sala} for b in bienes],
            },
        )
        print(f"  acta {acta}: un oficial de {quien} devolvió un arma, aplicada")
        return creada["id"], oficial_id

    def cargar_actas(self):
        print("Aplicada y revisada")
        acta = self.entregar(
            "a",
            "b",
            ARMAMENTO,
            2,
            "0101/2026",
            "Armas para el refuerzo del turno noche",
            20,
        )
        if acta:
            self.aceptar("b", acta)
            self.revisar("norte", acta)

        print("Aplicada y observada (la unidad todavía no la corrige)")
        acta = self.entregar(
            "a", "b", CHALECOS, 2, "0102/2026", "Chalecos de recambio", 18
        )
        if acta:
            self.aceptar("b", acta)
            self.revisar(
                "norte", acta, "El número de acta no coincide con el acta escaneada"
            )

        print("Observada, rectificada y revisada")
        acta = self.entregar(
            "b", "a", EQUIPOS, 1, "0103/2026", "Equipo vehicular para patrulla", 16
        )
        if acta:
            self.aceptar("a", acta)
            self.revisar(
                "norte", acta, "La fecha del hecho difiere de la del acta firmada"
            )
            self.rectificar(
                "b",
                acta,
                "Se corrigió la fecha según el acta firmada",
                "Equipo vehicular para patrulla (fecha corregida)",
                17,
            )
            self.revisar("norte", acta)

        print("Aplicada, pendiente de revisión de la Regional Norte")
        acta = self.entregar(
            "a", "b", MOVILES, 1, "0104/2026", "Móvil para traslados", 12
        )
        if acta:
            self.aceptar("b", acta)

        print("Aplicada, pendiente de revisión de la Regional Sur")
        acta = self.entregar(
            "c", "a", ARMAMENTO, 1, "0105/2026", "Arma de la Regional Sur", 10
        )
        if acta:
            self.aceptar("a", acta)

        print("Aplicada de Dirección (no se revisa)")
        acta = self.entregar(
            "direccion", "a", ARMAMENTO, 2, "0106/2026", "Armamento de la Dirección", 9
        )
        if acta:
            self.aceptar("a", acta)

        print("Pendientes de recepción")
        self.entregar(
            "a", "c", ARMAMENTO, 1, "0107/2026", "Armamento para la Operacional C", 3
        )
        self.entregar(
            "b", "a", CHALECOS, 1, "0108/2026", "Chaleco para la Operacional A", 2
        )
        self.entregar(
            "c", "b", MOVILES, 1, "0109/2026", "Móvil para la Operacional B", 1
        )

        print("Devuelta al origen (queda para corregir)")
        acta = self.entregar(
            "b", "c", ARMAMENTO, 1, "0110/2026", "Armamento para la Operacional C", 7
        )
        if acta:
            self.devolver_al_origen(
                "c", acta, "El número de serie del arma no coincide con el acta"
            )

        print("Rechazada (el origen desiste)")
        acta = self.entregar(
            "c", "b", CHALECOS, 1, "0111/2026", "Chaleco para la Operacional B", 6
        )
        if acta:
            self.devolver_al_origen("b", acta, "El chaleco llegó vencido")
            self.pedir(
                "c",
                "POST",
                f"/movimientos/{acta}/desistimiento",
                {"motivo": "Se desiste de la entrega, el chaleco se da de baja"},
            )
            print("    rechazada: la unidad de origen desistió")

    def cargar_dotaciones(self):
        print("Devolución de un oficial y nueva dotación")
        acta, oficial_id = self.devolucion_de_oficial(
            "a", "0112/2026", "El oficial devolvió el arma por licencia", 5
        )
        if acta:
            self.revisar("norte", acta)
            self.dotar(
                "a",
                ARMAMENTO,
                "0113/2026",
                "Arma asignada al oficial al volver de licencia",
                3,
                oficial_id,
            )
        print("Dotación pendiente de revisión")
        self.dotar(
            "b",
            EQUIPOS,
            "0114/2026",
            "Portátil asignado al oficial para el servicio",
            2,
        )

    def cargar(self):
        self.cargar_actas()
        self.cargar_dotaciones()


def main():
    demo = Demo()
    if sys.argv[1:] == ["dotaciones"]:
        demo.cargar_dotaciones()
        return 0
    if (
        llamar(
            "GET", "/movimientos/3", demo.tokens["direccion"], esperado=(200, 403, 404)
        )[0]
        == 200
    ):
        print("La base ya tiene actas de demostración, no se cargó nada.")
        return 0
    try:
        demo.cargar()
    except Fallo as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Datos de demostración cargados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
