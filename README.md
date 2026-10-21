# Sistema Logístico Policial

Trabajo Final Integrador de la Tecnicatura Universitaria en Programación a Distancia, Universidad Tecnológica Nacional.

Grupo 161: Mariano Rodríguez Arce y Raul Robino.

## Descripción

Sistema web que centraliza la trazabilidad de los bienes logísticos de una fuerza de seguridad: armamento, chalecos balísticos, móviles y equipos de comunicaciones. Registra quién tiene cada bien, dónde está, qué movimientos tuvo y qué actas los respaldan, y permite que el nivel superior revise lo que cargan las unidades que dependen de él. Lo usa el personal logístico de la Dirección Logística, de las Unidades Regionales y de las Unidades Operacionales.

La organización y todos los datos del proyecto son ficticios.

## Estado del proyecto

Terminamos el análisis y el diseño y estamos en la codificación. Ya están la base del backend, el esquema de la base de datos, los datos de prueba, las pruebas automatizadas y la integración continua.

El desarrollo se organiza en sprints. Cada historia de usuario y cada tarea técnica es un issue de GitHub con sus criterios y su estimación. Se trabaja en una rama propia y entra a main por un PR, con los linters y las pruebas corriendo en GitHub Actions.

## Tecnologías

| Componente | Tecnología |
|---|---|
| Base de datos | MySQL 8 |
| Backend | Python con FastAPI, Pydantic y SQLModel |
| Estructura de la base | Scripts SQL versionados en /database |
| Autenticación | JWT |
| Frontend | React con TypeScript y Tailwind |
| Pruebas | pytest |

La justificación de cada tecnología está en la sección 5 del documento de diseño.

## Estructura del repositorio

```text
/docs                  entregas, documento de diseño, diagrama entidad-relación e historias
  /decisiones          decisiones de arquitectura, una por archivo
/database
  /migraciones         scripts de creación de la base, numerados en orden
  /semillas            carga inicial de unidades, oficiales y bienes
/backend
  /app                 un paquete por módulo
  /tests               pruebas automatizadas
/frontend              aplicación React con TypeScript y Tailwind
```

Las historias de usuario y las reglas de negocio están en [docs/historias_y_reglas.md](docs/historias_y_reglas.md).

## Entregas

### Primera entrega: definición del problema y propuesta de MVP

- [Definición del problema](docs/1ra%20Entrega%20-%20Analisis%20-%20Proyecto%20Final%20-%20Grupo%20161.md)
- [Propuesta de MVP](docs/1ra%20Entrega%20-%20Propuesta%20de%20MVP%20-%20Proyecto%20Final%20-%20Grupo%20161.md)

### Segunda entrega: diseño y módulos

- [Documento de diseño y módulos](docs/2da%20Entrega%20-%20Diseno%20y%20modulos%20-%20Proyecto%20Final%20-%20Grupo%20161.md)
- [Diagrama entidad-relación](docs/diagrama_entidad_relacion.png)
- [Script de creación de la base de datos](database/migraciones/001_esquema.sql)

## Desarrollo local

Hace falta Docker y Python 3.13 o superior.

1. Copiar `.env.example` como `.env` y completar las contraseñas. Si el puerto 3306 está ocupado, cambiar `MYSQL_PUERTO` y el puerto de `DATABASE_URL`. `CLAVE_JWT` es la clave que firma los tokens de sesión y tiene que tener al menos 32 caracteres. Se puede generar con `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
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

## Datos de prueba

El script `database/semillas/cargar_datos_prueba.py` carga una organización ficticia para desarrollar y para la demo. Tiene la Dirección Logística, la Unidad Regional Norte con las Operacionales A y B, y la Unidad Regional Sur con la Operacional C. Cada unidad tiene sus ubicaciones, sus oficiales y bienes de los cuatro tipos en depósito y en dotación, 252 en total. En la Operacional A hay un arma dada de baja y una entrega de dos armas a B pendiente de recepción.

1. Completar `CONTRASENA_DEMO` en el `.env`. Es la contraseña de todos los usuarios de demo.
2. Con la base de desarrollo creada y el entorno virtual activo, correr desde la raíz del repositorio:

```bash
python database/semillas/cargar_datos_prueba.py
```

El script solo carga si la base está vacía. Si ya tiene datos, avisa y no modifica nada. Para cargarlos de nuevo hay que recrear la base como se explica en el desarrollo local. Siempre se cargan los mismos datos, así los ejemplos de la demo no cambian.

| Usuario | Unidad |
|---|---|
| `logistico.direccion` | Dirección Logística |
| `logistico.regional_norte` | Unidad Regional Norte |
| `logistico.regional_sur` | Unidad Regional Sur |
| `aux.unidad_a` | Unidad Operacional A |
| `aux.unidad_b` | Unidad Operacional B |
| `aux.unidad_c` | Unidad Operacional C |

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
