import os

from dotenv import load_dotenv

load_dotenv()
os.environ["DATABASE_URL"] = os.environ["DATABASE_URL_PRUEBAS"]
