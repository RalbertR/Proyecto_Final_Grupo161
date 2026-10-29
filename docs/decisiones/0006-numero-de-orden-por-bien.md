# 6. Número de orden de aplicación por bien

Aceptada el 29/10/2026.

## Contexto

Para saber qué movimiento o cambio de estado se aplicó antes sobre un bien no alcanza con la fecha del hecho, porque guarda solo el día y en un mismo día un bien puede entregarse, recibirse y asignarse. Tampoco sirve la fecha de carga, porque una entrega se carga cuando sale de la unidad de origen y se aplica cuando la recibe la de destino.

## Decisión

Cada bien tiene un contador, `ultimo_orden`, que la base aumenta con triggers cada vez que se le aplica un movimiento o un cambio de estado. El valor nuevo se guarda en `movimiento_bien.orden` o en `cambio_estado_operativo.orden`, y una restricción `UNIQUE` impide que se repita para el mismo bien.

- Un renglón que se inserta en un movimiento ya aplicado toma el número en el momento.
- Los renglones de una entrega pendiente quedan sin número y lo toman todos juntos cuando la cabecera pasa a aplicada.
- Una entrega rechazada no toma número y una anulación conserva el que tenía.

La API nunca escribe estas columnas.

## Consecuencias

El orden no depende de que cada operación se acuerde de numerar. Dos operaciones simultáneas sobre el mismo bien tampoco pueden tomar el mismo número, porque el trigger actualiza la fila del bien y la deja bloqueada hasta que termina la transacción.

A cambio, los renglones no se pueden cargar con `INSERT ... SELECT` desde la tabla `bien`. MySQL no deja que un trigger modifique una tabla que está leyendo la misma sentencia y responde con el error 1442.

El script 002 numera también los movimientos aplicados que ya existían, según la fecha del hecho, la de carga y el id.
