# Sistema Logístico Policial

Trabajo Final Integrador de la Tecnicatura Universitaria en Programación a Distancia, Universidad Tecnológica Nacional.

Grupo 161: Mariano Rodríguez Arce y Raul Robino.

## Descripción

Sistema web que centraliza la trazabilidad de los bienes logísticos de una fuerza de seguridad: armamento, chalecos balísticos, móviles y equipos de comunicaciones. Registra quién tiene cada bien, dónde está, qué movimientos tuvo y qué actas los respaldan, y permite que el nivel superior revise lo que cargan las unidades que dependen de él. Lo usa el personal logístico de la Dirección Logística, de las Unidades Regionales y de las Unidades Operacionales.

La organización y todos los datos del proyecto son ficticios.

## Estado del proyecto

Estamos en la etapa de análisis y diseño. El repositorio tiene la documentación, el script de la base de datos y la estructura de carpetas, todavía sin código. La codificación empieza cuando el tutor apruebe la segunda entrega.

## Tecnologías

| Componente | Tecnología |
|---|---|
| Base de datos | MySQL 8 |
| Backend | Python con FastAPI, Pydantic y SQLModel |
| Estructura de la base | Scripts SQL versionados en /database |
| Autenticación | JWT |
| Frontend | React con Tailwind |

La justificación de cada tecnología está en la sección 5 del documento de diseño.

## Estructura del repositorio

```text
/docs                  entregas, documento de diseño y diagrama entidad-relación
/database
  /migraciones         scripts de creación de la base, numerados en orden
  /semillas            carga inicial de unidades, oficiales y bienes
/backend
  /app                 un paquete por módulo
  /tests               pruebas automatizadas
/frontend              aplicación React con Tailwind
```

## Entregas

### Primera entrega: definición del problema y propuesta de MVP

- [Definición del problema](docs/1ra%20Entrega%20-%20Analisis%20-%20Proyecto%20Final%20-%20Grupo%20161.md)
- [Propuesta de MVP](docs/1ra%20Entrega%20-%20Propuesta%20de%20MVP%20-%20Proyecto%20Final%20-%20Grupo%20161.md)

### Segunda entrega: diseño y módulos

- [Documento de diseño y módulos](docs/Diseno%20y%20modulos%20-%20Proyecto%20Final%20-%20Grupo%20161.md)
- [Diagrama entidad-relación](docs/diagrama_entidad_relacion.png)
- [Script de creación de la base de datos](database/migraciones/001_esquema.sql)

## Desarrollo local

Hace falta Docker y Python 3.13 o superior.

1. Copiar `.env.example` como `.env` y completar las contraseñas. Si el puerto 3306 está ocupado, cambiar `MYSQL_PUERTO` y el puerto de `DATABASE_URL`.
2. Levantar MySQL con `docker compose up -d`. La primera vez crea la base con los scripts de `database/migraciones`.
3. Crear el entorno virtual del backend, instalar las dependencias y levantar la API:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
fastapi dev app/main.py
```

En Linux o macOS el entorno se activa con `source .venv/bin/activate`.

4. Abrir `http://localhost:8000/api/salud`, que tiene que responder `{"estado":"ok"}`. La documentación de la API está en `http://localhost:8000/docs`.

Los scripts solo se ejecutan cuando el volumen de MySQL está vacío. Para recrear la base desde cero hay que correr `docker compose down -v` y después `docker compose up -d`.

5. Activar pre-commit una sola vez, desde la raíz del repositorio y con el entorno virtual activo, para que Black y Ruff revisen el código en cada commit:

```bash
pip install pre-commit
pre-commit install
```

Para revisar todo el repositorio sin hacer un commit: `pre-commit run --all-files`.

## Pruebas

Las pruebas usan una base MySQL propia, separada de la de desarrollo, porque antes de cada prueba se vacían todas las tablas. Se crea con los mismos scripts de `database/migraciones` y guarda los datos en memoria. La conexión se toma de `DATABASE_URL_PRUEBAS` y, si el puerto 3308 está ocupado, hay que cambiar `MYSQL_PUERTO_PRUEBAS` y el puerto de esa URL.

1. Levantar la base de prueba. El comando espera a que la base termine de crearse:

```bash
docker compose up -d --wait mysql_pruebas
```

2. Desde `backend` y con el entorno virtual activo, instalar las dependencias de desarrollo y correr las pruebas con la cobertura:

```bash
pip install -r requirements-dev.txt
pytest --cov=app --cov-report=term-missing
```

La salida de este comando es la que se pega en cada PR.

La base de prueba se crea de nuevo cada vez que arranca el contenedor. Cuando se agrega un script a `database/migraciones`, alcanza con `docker compose up -d --wait --force-recreate mysql_pruebas`. Para apagarla se usa `docker compose stop mysql_pruebas`, porque un `docker compose down` no la incluye.

## Licencia

[MIT](LICENSE).
