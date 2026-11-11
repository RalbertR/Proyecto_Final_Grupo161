# Sistema Logístico Policial

Trabajo Final Integrador de la Tecnicatura Universitaria en Programación a Distancia, Universidad Tecnológica Nacional.

Grupo 161: Mariano Rodríguez Arce y Raul Robino.

## Descripción

Sistema web que centraliza la trazabilidad de los bienes logísticos de una fuerza de seguridad: armamento, chalecos balísticos, móviles y equipos de comunicaciones. Registra quién tiene cada bien, dónde está, qué movimientos tuvo y qué actas los respaldan, y permite que el nivel superior revise lo que cargan las unidades que dependen de él. Lo usa el personal logístico de la Dirección Logística, de las Unidades Regionales y de las Unidades Operacionales.

La organización y todos los datos del proyecto son ficticios.

### Qué hace

- **Inventario por alcance.** Una Unidad Operacional ve solo sus bienes, una Regional los suyos y los de sus Operacionales, y la Dirección los de todas (RN-01).
- **Entregas entre unidades.** Se registra el acta, el destino la acepta ubicando cada bien o la devuelve al origen con un motivo, y el origen la corrige y la reenvía o desiste.
- **Dotación y devolución de oficiales.** Se asignan bienes a un oficial de la unidad y se registra cuando los devuelve.
- **Revisión.** El superior inmediato revisa u observa lo que cargan sus unidades. Una corrección nunca pisa el original: queda como una versión nueva.
- **Actas escaneadas.** Se adjunta el PDF firmado a cada movimiento y la Regional lo ve al lado de los datos que revisa.
- **Estado de servicio.** Un bien pasa a fuera de servicio con su informe técnico, o vuelve a servicio.
- **Historial y control.** Cada bien tiene su historial y su línea de custodia, y la Regional y la Dirección tienen una sala de situación con las actas demoradas y el equipamiento fuera de servicio.

Las historias de usuario y las reglas están en [docs/historias_y_reglas.md](docs/historias_y_reglas.md).

## Sistema desplegado

El sistema está publicado en **https://logistica.nano-rodriguez.com**. Se entra con cualquiera de los usuarios de demostración, todos con la contraseña `1234Test`.

| Usuario | Unidad | Qué puede hacer |
|---|---|---|
| `aux.unidad_a` | Unidad Operacional A | Registrar entregas, recibir las que le llegan, asignar bienes a oficiales y registrar sus devoluciones, cambiar el estado de servicio y corregir lo que le observan. |
| `aux.unidad_b` | Unidad Operacional B | Lo mismo que la Operacional A. |
| `aux.unidad_c` | Unidad Operacional C | Lo mismo que la Operacional A, dentro de la Regional Sur. |
| `logistico.regional_norte` | Unidad Regional Norte | Revisar lo que registran las Operacionales A y B, con el acta escaneada al lado, ver el inventario propio y el de sus unidades, ver la sala de situación y operar sus propios bienes. |
| `logistico.regional_sur` | Unidad Regional Sur | Lo mismo que la Regional Norte, con la Operacional C. |
| `logistico.direccion` | Dirección Logística | Revisar lo que registran las Regionales, ver el inventario de toda la organización y la sala de situación, y operar sus propios bienes. |

Para ver el recorrido principal, `aux.unidad_a` elige dos armas en depósito desde el inventario y registra una entrega a la Unidad Operacional B. Después `aux.unidad_b` la recibe desde "Por recibir" y `logistico.regional_norte` la revisa desde "Revisión". En la página de cada arma queda la línea de custodia con el paso de A a B.

## Estado del proyecto

La versión 1.0 está terminada y desplegada, con todo lo que se describe en [Qué hace](#qué-hace). Los traslados, las anulaciones de actas, las reubicaciones, las altas, las bajas y los reportes quedaron para una versión siguiente.

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
- [Diagrama entidad-relación](docs/2da%20Entrega%20-%20Diseno%20y%20modulos%20-%20Proyecto%20Final%20-%20Grupo%20161.md#diagrama-entidad-relación)
- [Script de creación de la base de datos](database/migraciones/001_esquema.sql)

## Desarrollo local

Hace falta Docker, Python 3.13 o superior, Node 22 o superior y pnpm. Si pnpm no está instalado, se instala con `npm install -g pnpm`.

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

4. Abrir `http://localhost:8000/api/salud`, que tiene que responder `{"estado":"ok"}`. La documentación de la API está en `http://localhost:8000/api/docs`, como se explica en [Documentación de la API](#documentación-de-la-api).

Los scripts solo se ejecutan cuando el volumen de MySQL está vacío. Para recrear la base desde cero hay que correr `docker compose down -v` y después `docker compose up -d`.

5. Con la API levantada, abrir otra terminal, instalar las dependencias del frontend y levantarlo:

```bash
cd frontend
pnpm install
pnpm dev
```

La aplicación queda en `http://localhost:5173`. El servidor de Vite reenvía a la API todo lo que empieza con `/api`, así que sin el backend levantado las pantallas no cargan datos. Antes de abrir un PR hay que correr `pnpm lint` y `pnpm format:check`, que son los que corre la integración continua.

6. Activar pre-commit una sola vez, desde la raíz del repositorio y con el entorno virtual activo, para que Black y Ruff revisen el código en cada commit:

```bash
pip install pre-commit
pre-commit install
```

Para revisar todo el repositorio sin hacer un commit: `pre-commit run --all-files`.

## Documentación de la API

Swagger explica cada endpoint con su descripción, un ejemplo de lo que recibe o devuelve y los errores que puede responder, con el mensaje de cada uno. Está en `/api/docs`, y `/api/redoc` muestra lo mismo en otro formato:

| Dónde | Dirección |
|---|---|
| Desarrollo, directo al backend | `http://localhost:8000/api/docs` |
| Desarrollo, por el servidor de Vite | `http://localhost:5173/api/docs` |
| Servidor | `https://logistica.nano-rodriguez.com/api/docs` |

Para probar los endpoints desde esa página:

1. Tocar **Authorize**, escribir un usuario de la tabla de [datos de prueba](#datos-de-prueba) (por ejemplo `aux.unidad_a`) y la `CONTRASENA_DEMO` del `.env`, y confirmar. Los demás endpoints envían el token solos.
2. Abrir un endpoint, tocar **Try it out** y **Execute**. Lo que se ve depende del usuario: una Operacional solo ve su unidad, y el mismo pedido con otro usuario da otro resultado.

Los errores de negocio responden siempre `{"detail": "<texto en español>"}`:

| Código | Cuándo |
|---|---|
| 401 | Falta el token, es inválido o venció. |
| 403 | El usuario no tiene alcance sobre lo que pide. |
| 404 | El recurso no existe. |
| 409 | El estado actual no admite la operación: un bien con un movimiento pendiente, un acta ya resuelta, una versión vencida. |
| 422 | Un dato no cumple el formato o una regla de validación. Si falla el formato, `detail` es una lista con el campo que falló. |

Los contratos con más detalle están en [docs/contratos](docs/contratos): [actas escaneadas](docs/contratos/documentos.md), [cambios de estado](docs/contratos/cambios_estado.md) y [sala de situación](docs/contratos/situacion.md). Una prueba de pytest falla si se agrega un endpoint sin descripción, sin ejemplo o sin sus errores, así que la documentación no se puede quedar atrás.

## Actas escaneadas

La API permite adjuntar PDFs a un movimiento ya registrado y descargarlos con los mismos permisos de consulta del acta. Solo la unidad que registró el movimiento puede adjuntar. El contrato y los errores están en [HU-13: documentos de las actas](docs/contratos/documentos.md).

En la aplicación, la sección "PDFs del acta" permite adjuntar después del registro y desde el detalle del acta. También está disponible al recibir, revisar y corregir. Cada documento muestra su nombre, tamaño, usuario y fecha, con la opción de descargarlo.

En desarrollo, los PDFs se guardan en `backend/archivos_privados/documentos`, una carpeta ignorada por Git. Para usar otra carpeta privada, definir `DIRECTORIO_DOCUMENTOS` en el `.env`. En producción se guardan en el volumen `documentos_privados`, montado solo en el backend; el contenedor corre como `nobody` y puede escribir allí. Ese volumen conserva los archivos al recrear el backend y se debe respaldar junto con MySQL.

## Cambios de estado de servicio

En la página de un bien, la sección "Estado de servicio" permite pasarlo a fuera de servicio con observaciones y el informe técnico en PDF, o volverlo a servicio con observaciones y, si se tiene, un informe de puesta en servicio. El superior lo confirma u observa desde la bandeja de revisión, y la unidad corrige los observados desde "Observados". Los informes se guardan igual que las actas escaneadas. El contrato y los errores están en [HU-17: cambios de estado de servicio](docs/contratos/cambios_estado.md).

## Datos de prueba

El script `database/semillas/cargar_datos_prueba.py` carga una organización ficticia para desarrollar y para la demo. Tiene la Dirección Logística, la Unidad Regional Norte con las Operacionales A y B, y la Unidad Regional Sur con la Operacional C. Cada unidad tiene sus ubicaciones, sus oficiales y bienes de los cuatro tipos en depósito y en dotación, 252 en total. En la Operacional A hay un arma dada de baja y una entrega de dos armas a B pendiente de recepción.

1. Completar `CONTRASENA_DEMO` en el `.env`. Es la contraseña de todos los usuarios de demo.
2. Con la base de desarrollo creada y el entorno virtual activo, correr desde la raíz del repositorio:

```bash
python database/semillas/cargar_datos_prueba.py
```

El script solo carga si la base está vacía. Si ya tiene datos, avisa y no modifica nada. Para cargarlos de nuevo hay que recrear la base como se explica en el desarrollo local. Siempre se cargan los mismos datos, así los ejemplos de la demo no cambian.

Son los mismos usuarios del [sistema desplegado](#sistema-desplegado). Esta tabla cuenta lo que ve cada uno con los datos recién cargados:

| Usuario | Unidad | Qué puede hacer |
|---|---|---|
| `logistico.direccion` | Dirección Logística | Ve todas las unidades. Revisa lo que registran las Regionales. Lo que registra no se revisa. |
| `logistico.regional_norte` | Unidad Regional Norte | Ve la Regional, A y B. Revisa lo que registran A y B. |
| `logistico.regional_sur` | Unidad Regional Sur | Ve la Regional y C. Revisa lo que registra C. |
| `aux.unidad_a` | Unidad Operacional A | Ve solo A. Tiene un arma dada de baja y una entrega a B pendiente de recepción. |
| `aux.unidad_b` | Unidad Operacional B | Ve solo B. Recibe la entrega de A. |
| `aux.unidad_c` | Unidad Operacional C | Ve solo C. Sirve para comprobar que no accede a los bienes de A. |

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

El frontend no tiene pruebas automáticas: la integración continua corre `pnpm lint` y `pnpm format:check` desde `frontend`, y las pantallas se prueban a mano contra los criterios de [docs/historias_y_reglas.md](docs/historias_y_reglas.md). Los linters del backend se corren con `pre-commit run --all-files`.

La base de prueba se crea de nuevo cada vez que arranca el contenedor. Cuando se agrega un script a `database/migraciones`, alcanza con `docker compose up -d --wait --force-recreate mysql_pruebas`. Para apagarla se usa `docker compose stop mysql_pruebas`, porque un `docker compose down` no la incluye.

## Despliegue

El sistema se publica en una VM con Docker, con `docker-compose.prod.yml`. Corren tres contenedores: MySQL, el backend y nginx con el build del frontend. nginx sirve la aplicación en `/` y pasa `/api` al backend. MySQL no expone puertos. nginx publica el puerto 80 de la VM, y desde afuera se entra por el Cloudflare Tunnel que ya corre en el homelab, que da HTTPS sin abrir puertos en el router.

La primera vez que arranca, MySQL crea la base con los scripts de `database/migraciones` y `database/iniciar_produccion.sh` deja al usuario de la aplicación solo con `SELECT`, `INSERT`, `UPDATE` y `DELETE` sobre la base. El backend nunca usa root.

1. Crear la VM con Debian o Ubuntu (2 GB de RAM y 15 GB de disco alcanzan) e instalar Docker con el plugin compose y git.
2. En el panel de Cloudflare, ir a Zero Trust, Networks, Tunnels, abrir el túnel del homelab y agregar un Public Hostname con el subdominio y el dominio, servicio `HTTP` y URL `<IP de la VM>:80`. Usar un subdominio que no tenga ya un registro DNS.
3. Clonar el repositorio en la VM y crear el `.env` en la raíz. Los secretos viven solo en ese archivo, que no se sube al repositorio:

```bash
COMPOSE_FILE=docker-compose.prod.yml
MYSQL_ROOT_PASSWORD=
MYSQL_USER=logistica
MYSQL_PASSWORD=
CLAVE_JWT=
CONTRASENA_DEMO=
```

Cada contraseña y la clave JWT se generan con `openssl rand -hex 32`. La contraseña de MySQL va dentro de la URL de conexión, por eso tiene que ser hexadecimal y sin símbolos. `COMPOSE_FILE` hace que todos los `docker compose` usen el archivo de producción sin tener que pasar `-f`. Después de completarlo, correr `chmod 600 .env`.

4. Levantar todo con `docker compose up -d --build` y revisar con `docker compose ps` que los contenedores estén corriendo y MySQL figure `healthy`.
5. Abrir `https://<subdominio>/api/salud`, que tiene que responder `{"estado":"ok"}`, y después `https://<subdominio>` para ver el login. La documentación de la API queda en `https://<subdominio>/api/docs`.
6. Para la demo, cargar los datos de prueba con `docker compose run --rm semillas`. Usa la `CONTRASENA_DEMO` del `.env`.
7. Para recorrer todas las funciones, completar la demo con actas en todos los estados (backend levantado). Los tres comandos van en este orden y cada uno se corre **una sola vez**: `historia` no es idempotente y correrla dos veces duplica eventos.

```bash
docker compose run --rm semillas python /semillas/cargar_demo.py
docker compose run --rm semillas python /semillas/cargar_historia.py historia
docker compose run --rm semillas python /semillas/cargar_historia.py cerrar
```

`cargar_demo.py` registra por la API las actas pendientes de recepción, aplicadas, rechazadas, devueltas, revisadas, observadas y rectificadas, y las dotaciones a oficiales. `cargar_historia.py` agrega una historia de julio a noviembre de 2026 fechada por SQL, y `cerrar` numera las actas por unidad en orden cronológico y adjunta el acta escaneada de cada una. Si hay que repetirlo, se recrea la base como se explica más abajo. Antes de tocar datos en el servidor conviene hacer un respaldo.

8. Programar el respaldo diario de la base (ver la sección siguiente).

### Respaldo y restauración

`database/respaldar.sh` hace un `mysqldump` comprimido de la base y lo guarda en `~/respaldos/logistica_<fecha>.sql.gz` con permisos `600`. Conserva los últimos siete, borra los más viejos y descarta un volcado incompleto en vez de dejarlo como respaldo. Para correrlo a las 3:00 todos los días, agregar con `crontab -e`:

```
0 3 * * * sh /home/<usuario>/proyecto_final/Proyecto_Final_Grupo161/database/respaldar.sh >> /home/<usuario>/respaldos/respaldo.log 2>&1
```

Se puede correr a mano en cualquier momento con `sh database/respaldar.sh`. El respaldo guarda la base, no los PDFs de las actas, que están en el volumen `documentos_privados` y se respaldan aparte.

Para comprobar que un respaldo sirve sin tocar la base real, se restaura en una base temporal y se comparan los datos:

```bash
docker compose exec -T mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "CREATE DATABASE restauracion_prueba"'
gzip -dc ~/respaldos/logistica_<fecha>.sql.gz | docker compose exec -T mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" restauracion_prueba'
docker compose exec -T mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "DROP DATABASE restauracion_prueba"'
```

Entre el segundo y el tercer comando, comparar con `SELECT COUNT(*)` las tablas `movimiento`, `bien`, `documento` y `revision`, y los triggers en `information_schema.triggers`, contra `logistica_policial`. Esta prueba se hizo el 11 de noviembre de 2026 con el respaldo del servidor y dio los mismos conteos: 69 movimientos, 252 bienes, 79 documentos, 57 revisiones y 11 triggers.

Para restaurar de verdad (por ejemplo, después de una migración que falló), frenar el backend, borrar la base y cargar el respaldo en `logistica_policial`:

```bash
docker compose stop backend
docker compose exec -T mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "DROP DATABASE logistica_policial; CREATE DATABASE logistica_policial"'
gzip -dc ~/respaldos/logistica_<fecha>.sql.gz | docker compose exec -T mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" logistica_policial'
docker compose up -d
```

Como el respaldo no trae `CREATE DATABASE`, hay que recrear la base vacía antes. Los permisos del usuario de la aplicación se conservan.

### Actualizar el servidor

Para pasar a una versión nueva, correr `git pull` y `docker compose up -d --build`. Si el `git pull` trae un script nuevo en `database/migraciones`, hay que aplicarlo antes del `up`. MySQL solo corre esos scripts la primera vez, con el volumen vacío.

Los scripts los aplica root, porque el usuario de la aplicación no puede cambiar el esquema. La contraseña de root ya está en el contenedor de MySQL, que la toma del `.env`, y la carpeta `database/migraciones` está montada en `/migraciones`, así que después del `git pull` el contenedor ya ve el script nuevo.

| Script | Qué cambia |
|---|---|
| `001_esquema.sql` | Crea las tablas, las vistas y los triggers. |
| `002_entregas_y_revision.sql` | Número de orden por bien, revisión de la versión vigente y jerarquía estricta. |
| `003_oficiales_y_cambios_de_estado.sql` | La unidad de un oficial solo cambia con un traslado, y las correcciones de un fuera de servicio llevan informe. |
| `004_devolucion_de_actas.sql` | Devolución del acta al origen. |
| `005_fechas_en_hora_argentina.sql` | El historial y la bandeja muestran el día de los cambios de estado en hora de Argentina. |

1. Frenar el backend para que nadie escriba mientras cambia el esquema:

```bash
docker compose stop backend
```

2. Guardar un respaldo de la base fuera del repositorio:

```bash
docker compose exec -T mysql sh -c 'mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --triggers --databases logistica_policial' > ~/respaldo_$(date +%F).sql
chmod 600 ~/respaldo_*.sql
```

3. Aplicar cada script nuevo, uno por vez y en orden de número:

```bash
docker compose exec -T mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" logistica_policial < /migraciones/005_fechas_en_hora_argentina.sql'
```

4. Levantar el backend con el código nuevo con `docker compose up -d --build` y verificar en `https://<subdominio>/api/salud` que responda.

Cada script se aplica una sola vez. Si se corre uno que ya está aplicado, falla en la primera sentencia con un error como `Duplicate column name` y no cambia nada. El 005 es la excepción, porque solo redefine vistas y se puede volver a correr sin que falle. Si un script falla en el medio, la base queda a medio cambiar, porque en MySQL los cambios de esquema no se pueden deshacer. En ese caso se restaura el respaldo:

```bash
docker compose exec -T mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "DROP DATABASE logistica_policial"'
docker compose exec -T mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' < ~/respaldo_<fecha>.sql
```

Los permisos del usuario de la aplicación no se pierden al borrar la base.

Para volver los datos de demo al estado inicial, por ejemplo después de probar el recorrido de entregas, se recrea la base desde cero. Así corren todos los scripts y se cargan los datos de demo de nuevo. **Esto borra todo lo cargado en el servidor.**

```bash
docker compose down -v
docker compose up -d --build
docker compose run --rm semillas
```

Los logs se ven con `docker compose logs -f backend`, o con el nombre de otro servicio.

## Licencia

[MIT](LICENSE).
