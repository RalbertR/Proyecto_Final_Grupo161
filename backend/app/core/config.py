import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
CLAVE_JWT = os.environ["CLAVE_JWT"]
DIRECTORIO_DOCUMENTOS = Path(
    os.environ.get("DIRECTORIO_DOCUMENTOS")
    or Path(__file__).resolve().parents[2] / "archivos_privados" / "documentos"
)
