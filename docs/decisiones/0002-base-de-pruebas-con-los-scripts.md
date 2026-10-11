# 2. Base de pruebas armada con los scripts

Aceptada el 11/10/2026.

## Contexto

Muchas reglas del modelo viven en la base: claves foráneas compuestas, restricciones `CHECK` y triggers. SQLModel puede crear las tablas a partir de los modelos con `create_all`, pero esas tablas no tienen los triggers ni los `CHECK`, y los modelos no cubren todo el esquema.

## Decisión

La base de pruebas se crea ejecutando en orden los scripts de `database/migraciones`, los mismos que usamos en desarrollo y en el servidor. Nunca usamos `create_all`.

## Consecuencias

Las pruebas corren contra el mismo esquema que producción y verifican también las reglas que aplica la base. A cambio, necesitan un MySQL real, que se levanta con docker compose en local y como servicio en el CI.
