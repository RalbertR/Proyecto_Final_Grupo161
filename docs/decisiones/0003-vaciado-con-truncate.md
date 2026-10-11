# 3. Vaciado de tablas con TRUNCATE entre pruebas

Aceptada el 11/10/2026.

## Contexto

Una forma común de aislar las pruebas es abrir una transacción al comienzo de cada una y deshacerla al final. La prueba de concurrencia usa dos conexiones que tienen que ver los datos que confirmó la otra, y eso no funciona si los datos de la prueba nunca se confirman.

## Decisión

Las pruebas confirman sus datos igual que la aplicación, y entre una prueba y otra vaciamos las tablas con `TRUNCATE`. Durante el vaciado se desactiva el control de claves foráneas.

## Consecuencias

Todas las pruebas funcionan de la misma manera, incluida la de concurrencia, y cada una arma los datos que necesita. Vaciar las tablas es más lento que deshacer una transacción, pero con el tamaño de este esquema es aceptable.
