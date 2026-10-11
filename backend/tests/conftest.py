import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, text

from app.core.database import engine
from app.main import create_app

TIPOS_DE_BIEN = [
    {"codigo": "ARMAMENTO", "nombre": "Armamento"},
    {"codigo": "CHALECO", "nombre": "Chaleco balístico"},
    {"codigo": "MOVIL", "nombre": "Móvil"},
    {"codigo": "EQUIPO_COMUNICACIONES", "nombre": "Equipo de comunicaciones"},
]


@pytest.fixture(scope="session")
def tablas():
    with engine.connect() as conexion:
        return (
            conexion.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE'"
                )
            )
            .scalars()
            .all()
        )


@pytest.fixture(autouse=True)
def base_vacia(tablas):
    with engine.begin() as conexion:
        conexion.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for tabla in tablas:
            conexion.execute(text(f"TRUNCATE TABLE {tabla}"))
        conexion.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conexion.execute(
            text("INSERT INTO tipo_bien (codigo, nombre) VALUES (:codigo, :nombre)"),
            TIPOS_DE_BIEN,
        )


@pytest.fixture
def session():
    with Session(engine) as session:
        yield session


@pytest.fixture
def client():
    with TestClient(create_app()) as client:
        yield client
