# 9. Unidad del oficial

Aceptada el 6/11/2026.

## Contexto

`bien` referencia a `oficial` con una clave compuesta y `ON UPDATE CASCADE`, así que al cambiar la unidad de un oficial sus dotaciones pasan a la unidad nueva. Eso es lo que hace falta al confirmar un traslado, pero un cambio directo movería bienes de unidad sin dejar ningún movimiento en el historial.

## Decisión

Un trigger en `oficial` rechaza el cambio de unidad si el oficial tiene bienes asignados o aparece como origen o destino de un movimiento, en cualquier estado, salvo que su último traslado confirmado vaya de la unidad actual a la nueva. Un oficial sin bienes ni movimientos cambia de unidad sin restricciones.

Se mira el último traslado confirmado y no cualquiera para que uno viejo no sirva de permiso. Si un oficial pasó de A a B y volvió de B a A, un cambio directo a B se rechaza aunque exista un traslado confirmado de A a B.

## Consecuencias

El módulo de Traslados tiene que seguir este orden en una sola transacción: primero marca el traslado como `CONFIRMADO` y después cambia la unidad del oficial. Al revés, el trigger lo rechaza.

Hasta que ese módulo exista, la unidad de un oficial con historial no cambia desde la aplicación.
