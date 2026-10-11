# 4. Scripts SQL ejecutados con el cliente mysql

Aceptada el 11/10/2026.

## Contexto

El script 001 define triggers y usa `DELIMITER` para cambiar el separador de sentencias. `DELIMITER` es un comando del cliente `mysql` y no de SQL, así que los drivers de Python como pymysql no lo entienden y fallan al ejecutar el script.

## Decisión

Los scripts de `database/migraciones` se ejecutan siempre con el cliente `mysql`. En docker compose se montan en `/docker-entrypoint-initdb.d` y la imagen oficial los ejecuta con ese cliente al crear la base. En el CI se ejecutan con `mysql ... < archivo.sql`.

## Consecuencias

Los scripts se escriben una sola vez y se ejecutan igual en desarrollo, en el CI y en el servidor. La imagen solo los ejecuta cuando el volumen está vacío, así que para aplicar un script nuevo sobre una base existente hay que ejecutarlo a mano o recrear el volumen.
