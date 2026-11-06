# 9. Unidad del oficial

Aceptada el 6/11/2026.

## Contexto

`bien` referencia a `oficial` con una clave compuesta y `ON UPDATE CASCADE`, así que al cambiar la unidad de un oficial sus dotaciones pasan a la unidad nueva. Eso es lo que hace falta al confirmar un traslado, pero un cambio directo movería bienes de unidad sin dejar ningún movimiento en el historial.

## Decisión

Un trigger en `oficial` rechaza el cambio de unidad si el oficial tiene bienes asignados, aparece como origen o destino de un movimiento en cualquier estado o tiene un traslado confirmado. La excepción es que su último traslado confirmado vaya de la unidad actual a la nueva y que todos sus bienes asignados estén en el movimiento de ese traslado. Un oficial sin bienes, movimientos ni traslados confirmados puede cambiar de unidad sin un traslado, porque no hay nada que quede sin registrar.

Se mira el último traslado confirmado y no cualquiera para que uno viejo no sirva de permiso. Si un oficial pasó de A a B y volvió de B a A, un cambio directo a B se rechaza aunque exista un traslado confirmado de A a B.

Un traslado confirmado cuenta como historial aunque el oficial no tenga dotaciones. Si no contara, el oficial podría ir de A a B, volver a A con un cambio directo, recibir un bien y usar ese mismo traslado para llevarlo a B.

Los bienes se controlan uno por uno porque un oficial puede recibir un bien mientras su traslado está pendiente. Ese bien no está en el movimiento del traslado y la cascada lo cambiaría de unidad sin dejar historial. Por la misma razón, un traslado sin movimiento solo sirve para un oficial sin dotaciones.

## Consecuencias

El módulo de Traslados tiene que seguir este orden en una sola transacción: primero marca el traslado como `CONFIRMADO` y después cambia la unidad del oficial. Al revés, el trigger lo rechaza.

Hasta que ese módulo exista, la unidad de un oficial con historial no cambia desde la aplicación.

Queda sin resolver cómo se anula un traslado ya confirmado. Al anularlo, el trigger rechaza la vuelta del oficial a su unidad anterior, porque ningún traslado confirmado lo lleva hasta ahí. Hay que definirlo cuando se haga el módulo de Traslados.
