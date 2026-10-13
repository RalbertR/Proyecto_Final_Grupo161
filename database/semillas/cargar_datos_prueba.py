import os
import random
import string
from datetime import date
from itertools import count

import bcrypt
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

TIPOS_DE_BIEN = [
    ("ARMAMENTO", "Armamento"),
    ("CHALECO", "Chaleco balístico"),
    ("MOVIL", "Móvil"),
    ("EQUIPO_COMUNICACIONES", "Equipo de comunicaciones"),
]

TIPOS_DE_VEHICULO = ["Camioneta", "Sedán", "Utilitario", "Motocicleta"]

TIPOS_DE_TAREA = [
    "Patrullaje",
    "Investigaciones",
    "Transporte de pasajeros",
    "Transporte de carga",
]

UNIDADES = [
    ("direccion", "Dirección Logística", "DIRECCION", None),
    ("norte", "Unidad Regional Norte", "REGIONAL", "direccion"),
    ("sur", "Unidad Regional Sur", "REGIONAL", "direccion"),
    ("a", "Unidad Operacional A", "OPERACIONAL", "norte"),
    ("b", "Unidad Operacional B", "OPERACIONAL", "norte"),
    ("c", "Unidad Operacional C", "OPERACIONAL", "sur"),
]

USUARIOS = {
    "direccion": "logistico.direccion",
    "norte": "logistico.regional_norte",
    "sur": "logistico.regional_sur",
    "a": "aux.unidad_a",
    "b": "aux.unidad_b",
    "c": "aux.unidad_c",
}

UBICACIONES = ["Sala de Armas", "Depósito", "Playón"]

DOTACION = {
    "direccion": {
        "oficiales": 8,
        "autos": 3,
        "motos": 0,
        "pistolas_en_deposito": 4,
        "escopetas": 2,
        "chalecos_en_deposito": 6,
        "portatiles_en_deposito": 4,
    },
    "norte": {
        "oficiales": 6,
        "autos": 2,
        "motos": 0,
        "pistolas_en_deposito": 2,
        "escopetas": 1,
        "chalecos_en_deposito": 2,
        "portatiles_en_deposito": 1,
    },
    "sur": {
        "oficiales": 6,
        "autos": 2,
        "motos": 0,
        "pistolas_en_deposito": 2,
        "escopetas": 1,
        "chalecos_en_deposito": 2,
        "portatiles_en_deposito": 1,
    },
    "a": {
        "oficiales": 16,
        "autos": 4,
        "motos": 2,
        "pistolas_en_deposito": 2,
        "escopetas": 2,
        "chalecos_en_deposito": 3,
        "portatiles_en_deposito": 2,
    },
    "b": {
        "oficiales": 14,
        "autos": 3,
        "motos": 1,
        "pistolas_en_deposito": 2,
        "escopetas": 1,
        "chalecos_en_deposito": 2,
        "portatiles_en_deposito": 2,
    },
    "c": {
        "oficiales": 12,
        "autos": 3,
        "motos": 1,
        "pistolas_en_deposito": 2,
        "escopetas": 1,
        "chalecos_en_deposito": 2,
        "portatiles_en_deposito": 1,
    },
}

APELLIDOS = [
    "Acosta",
    "Aguirre",
    "Álvarez",
    "Benítez",
    "Cabrera",
    "Castro",
    "Díaz",
    "Domínguez",
    "Escobar",
    "Fernández",
    "Ferreyra",
    "Flores",
    "Giménez",
    "Gómez",
    "González",
    "Herrera",
    "Ibarra",
    "Juárez",
    "Ledesma",
    "López",
    "Martínez",
    "Medina",
    "Molina",
    "Morales",
    "Navarro",
    "Pereyra",
    "Ramírez",
    "Romero",
    "Ruiz",
    "Sosa",
    "Suárez",
    "Torres",
    "Vega",
    "Villalba",
]

NOMBRES = [
    "Agustina",
    "Alejandro",
    "Andrea",
    "Carla",
    "Carlos",
    "Daniela",
    "Diego",
    "Emiliano",
    "Florencia",
    "Gabriel",
    "Gustavo",
    "Hernán",
    "Julián",
    "Laura",
    "Lucas",
    "Lucía",
    "Marcela",
    "Martín",
    "Matías",
    "Natalia",
    "Pablo",
    "Paula",
    "Romina",
    "Santiago",
    "Sebastián",
    "Sofía",
    "Tomás",
    "Valeria",
    "Verónica",
    "Walter",
]

PISTOLAS = [
    ("Bersa", "TPR9"),
    ("Bersa", "TPR9"),
    ("Bersa", "Thunder 9 Pro"),
    ("Glock", "17"),
]

ESCOPETAS = [("Mossberg", "500"), ("Remington", "870")]

CHALECOS = [("Táctico", "RB3"), ("Táctico", "RB3"), ("Encubierto", "RB2")]

TALLES = ["S", "M", "M", "L", "L", "XL"]

AUTOS = [
    ("Toyota", "Hilux", "Camioneta", "Patrullaje"),
    ("Ford", "Ranger", "Camioneta", "Patrullaje"),
    ("Peugeot", "408", "Sedán", "Patrullaje"),
    ("Chevrolet", "Cruze", "Sedán", "Investigaciones"),
    ("Renault", "Kangoo", "Utilitario", "Transporte de carga"),
    ("Mercedes-Benz", "Sprinter", "Utilitario", "Transporte de pasajeros"),
]

MOTOS = [("Honda", "XR 250 Tornado", "Motocicleta", "Patrullaje")]

PORTATILES = ["DEP 450", "DEP 550e"]

VEHICULARES = ["DEM 300", "DEM 400"]

BASES = ["DEM 500"]

PREFIJOS_DE_SERIE = {
    "Bersa": "BT",
    "Glock": "GL",
    "Taurus": "TA",
    "Mossberg": "MB",
    "Remington": "RM",
    "FM S.A.": "FM",
    "Motorola": "MT",
}

PREFIJOS_DE_PATENTE = {
    2019: "AD",
    2020: "AD",
    2021: "AE",
    2022: "AF",
    2023: "AF",
    2024: "AG",
}


class Carga:
    def __init__(self, conexion):
        self.conexion = conexion
        self.azar = random.Random(161)
        self.numeros_de_serie = {marca: count(100001) for marca in PREFIJOS_DE_SERIE}
        self.legajos = count(10001)
        self.numeros_internos = count(101)
        self.numeros_de_patente = count(104, 7)
        self.tipos_de_vehiculo = {}
        self.tipos_de_tarea = {}
        self.unidades = {}
        self.ubicaciones = {}
        self.usuarios = {}
        self.oficiales = {}

    def cargar(self, contrasena):
        self.cargar_catalogos()
        self.cargar_unidades(contrasena)
        for unidad, cantidades in DOTACION.items():
            self.cargar_bienes(unidad, cantidades)
        self.registrar_baja()
        self.registrar_entrega_pendiente()

    def insertar(self, tabla, **valores):
        columnas = ", ".join(valores)
        parametros = ", ".join(f":{columna}" for columna in valores)
        sentencia = text(f"INSERT INTO {tabla} ({columnas}) VALUES ({parametros})")
        return self.conexion.execute(sentencia, valores).lastrowid

    def cargar_catalogos(self):
        for codigo, nombre in TIPOS_DE_BIEN:
            self.insertar("tipo_bien", codigo=codigo, nombre=nombre)
        for nombre in TIPOS_DE_VEHICULO:
            self.tipos_de_vehiculo[nombre] = self.insertar(
                "tipo_vehiculo", nombre=nombre
            )
        for nombre in TIPOS_DE_TAREA:
            self.tipos_de_tarea[nombre] = self.insertar("tipo_tarea", nombre=nombre)

    def cargar_unidades(self, contrasena):
        hash_contrasena = bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()
        for clave, nombre, nivel, superior in UNIDADES:
            unidad_id = self.insertar(
                "unidad",
                nombre=nombre,
                nivel=nivel,
                unidad_superior_id=self.unidades.get(superior),
            )
            self.unidades[clave] = unidad_id
            for ubicacion in UBICACIONES:
                self.ubicaciones[(clave, ubicacion)] = self.insertar(
                    "ubicacion", unidad_id=unidad_id, nombre=ubicacion
                )
            self.usuarios[clave] = self.insertar(
                "usuario",
                nombre_usuario=USUARIOS[clave],
                hash_contrasena=hash_contrasena,
                unidad_id=unidad_id,
            )

    def cargar_bienes(self, unidad, cantidades):
        for numero in range(cantidades["oficiales"]):
            legajo = self.insertar_oficial(unidad)
            self.insertar_arma(unidad, legajo, PISTOLAS, "9x19mm", 34)
            self.insertar_chaleco(unidad, legajo)
            if numero % 2 == 0:
                self.insertar_equipo(unidad, legajo, PORTATILES, "PORTATIL")
        for _ in range(cantidades["autos"]):
            self.insertar_movil(unidad, AUTOS)
            self.insertar_equipo(unidad, "Playón", VEHICULARES, "VEHICULAR")
        for _ in range(cantidades["motos"]):
            self.insertar_movil(unidad, MOTOS)
        for _ in range(cantidades["pistolas_en_deposito"]):
            self.insertar_arma(unidad, "Sala de Armas", PISTOLAS, "9x19mm", 34)
        for _ in range(cantidades["escopetas"]):
            self.insertar_arma(unidad, "Sala de Armas", ESCOPETAS, "12/70", 12)
        for _ in range(cantidades["chalecos_en_deposito"]):
            self.insertar_chaleco(unidad, "Depósito")
        for _ in range(cantidades["portatiles_en_deposito"]):
            self.insertar_equipo(unidad, "Depósito", PORTATILES, "PORTATIL")
        self.insertar_equipo(unidad, "Depósito", BASES, "BASE")

    def insertar_oficial(self, unidad):
        legajo = str(next(self.legajos))
        self.oficiales[legajo] = self.insertar(
            "oficial",
            legajo=legajo,
            apellido=self.azar.choice(APELLIDOS),
            nombre=self.azar.choice(NOMBRES),
            unidad_id=self.unidades[unidad],
        )
        return legajo

    def insertar_bien(self, tipo_bien, unidad, tenencia, marca, modelo, serie=None):
        return self.insertar(
            "bien",
            tipo_bien=tipo_bien,
            marca=marca,
            modelo=modelo,
            numero_serie=serie,
            unidad_id=self.unidades[unidad],
            oficial_id=self.oficiales.get(tenencia),
            ubicacion_id=self.ubicaciones.get((unidad, tenencia)),
        )

    def numero_de_serie(self, marca):
        return f"{PREFIJOS_DE_SERIE[marca]}-{next(self.numeros_de_serie[marca])}"

    def insertar_arma(self, unidad, tenencia, modelos, calibre, cartuchos):
        marca, modelo = self.azar.choice(modelos)
        serie = self.numero_de_serie(marca)
        bien_id = self.insertar_bien(
            "ARMAMENTO", unidad, tenencia, marca, modelo, serie
        )
        self.insertar(
            "armamento", bien_id=bien_id, calibre=calibre, sbo_cartuchos=cartuchos
        )
        return bien_id

    def insertar_chaleco(self, unidad, tenencia):
        modelo, nivel = self.azar.choice(CHALECOS)
        serie = self.numero_de_serie("FM S.A.")
        bien_id = self.insertar_bien(
            "CHALECO", unidad, tenencia, "FM S.A.", modelo, serie
        )
        self.insertar(
            "chaleco",
            bien_id=bien_id,
            talle=self.azar.choice(TALLES),
            nivel_proteccion=nivel,
            fecha_vencimiento=date(
                self.azar.randint(2026, 2031), self.azar.randint(1, 12), 1
            ),
        )

    def insertar_movil(self, unidad, modelos):
        marca, modelo, tipo_vehiculo, tipo_tarea = self.azar.choice(modelos)
        anio = self.azar.randint(2019, 2024)
        bien_id = self.insertar_bien("MOVIL", unidad, "Playón", marca, modelo)
        self.insertar(
            "movil",
            bien_id=bien_id,
            patente=self.patente(anio, tipo_vehiculo),
            numero_interno=str(next(self.numeros_internos)),
            anio=anio,
            tipo_vehiculo_id=self.tipos_de_vehiculo[tipo_vehiculo],
            tipo_tarea_id=self.tipos_de_tarea[tipo_tarea],
        )

    def patente(self, anio, tipo_vehiculo):
        numero = next(self.numeros_de_patente)
        if tipo_vehiculo == "Motocicleta":
            return f"A{numero:03d}{self.letras(3)}"
        return f"{PREFIJOS_DE_PATENTE[anio]}{numero:03d}{self.letras(2)}"

    def letras(self, cantidad):
        return "".join(self.azar.choices(string.ascii_uppercase, k=cantidad))

    def insertar_equipo(self, unidad, tenencia, modelos, tipo_equipo):
        serie = self.numero_de_serie("Motorola")
        modelo = self.azar.choice(modelos)
        bien_id = self.insertar_bien(
            "EQUIPO_COMUNICACIONES", unidad, tenencia, "Motorola", modelo, serie
        )
        self.insertar("equipo_comunicaciones", bien_id=bien_id, tipo_equipo=tipo_equipo)

    def registrar_baja(self):
        sala_de_armas = self.ubicaciones[("a", "Sala de Armas")]
        bien_id = self.insertar_arma(
            "a", "Sala de Armas", [("Taurus", "PT92")], "9x19mm", 30
        )
        movimiento_id = self.insertar(
            "movimiento",
            tipo="BAJA",
            estado="APLICADO",
            estado_revision="PENDIENTE",
            numero_acta="0012/2026",
            fecha_hecho=date(2026, 9, 21),
            usuario_id=self.usuarios["a"],
            unidad_registrante_id=self.unidades["a"],
            unidad_origen_id=self.unidades["a"],
            motivo="Corredera fisurada, sin reparación posible según el armero",
        )
        self.insertar(
            "movimiento_bien",
            movimiento_id=movimiento_id,
            bien_id=bien_id,
            ubicacion_origen_id=sala_de_armas,
        )
        self.conexion.execute(
            text("UPDATE bien SET de_baja = TRUE, ubicacion_id = NULL WHERE id = :id"),
            {"id": bien_id},
        )

    def registrar_entrega_pendiente(self):
        sala_de_armas = self.ubicaciones[("a", "Sala de Armas")]
        armas = [
            self.insertar_arma("a", "Sala de Armas", PISTOLAS, "9x19mm", 34)
            for _ in range(2)
        ]
        movimiento_id = self.insertar(
            "movimiento",
            tipo="ENTREGA",
            estado="PENDIENTE",
            estado_revision="PENDIENTE",
            numero_acta="0015/2026",
            fecha_hecho=date(2026, 10, 9),
            usuario_id=self.usuarios["a"],
            unidad_registrante_id=self.unidades["a"],
            unidad_origen_id=self.unidades["a"],
            unidad_destino_id=self.unidades["b"],
            descripcion="Refuerzo de armamento para la Unidad Operacional B",
        )
        for bien_id in armas:
            self.insertar(
                "movimiento_bien",
                movimiento_id=movimiento_id,
                bien_id=bien_id,
                ubicacion_origen_id=sala_de_armas,
            )


def main():
    load_dotenv()
    contrasena = os.environ["CONTRASENA_DEMO"]
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.begin() as conexion:
        if conexion.execute(text("SELECT COUNT(*) FROM unidad")).scalar():
            print("La base ya tiene datos, no se cargó nada.")
            return
        Carga(conexion).cargar(contrasena)
    print("Datos de prueba cargados.")


if __name__ == "__main__":
    main()
