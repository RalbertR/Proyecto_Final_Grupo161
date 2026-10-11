# 1. Nivel de aislamiento READ COMMITTED

Aceptada el 11/10/2026.

## Contexto

Las operaciones que mueven bienes primero bloquean las filas con `SELECT ... FOR UPDATE` y después leen otros datos para validar las reglas, tanto en el servicio como en los triggers. InnoDB usa por defecto REPEATABLE READ, donde las lecturas comunes de una transacción ven los datos como estaban en su primera lectura. Si otra transacción confirma cambios mientras esperamos el bloqueo, la validación no los ve y puede aprobar una operación con datos viejos.

## Decisión

El engine de SQLModel abre todas las conexiones con el nivel `READ COMMITTED`.

## Consecuencias

Cada lectura ve los últimos datos confirmados, también después de esperar un bloqueo. La prueba de concurrencia, en la que dos usuarios intentan mover el mismo bien y solo uno lo logra, depende de este comportamiento. Dos lecturas iguales dentro de una misma operación pueden devolver valores distintos, por eso las filas que una operación necesita estables se bloquean con `FOR UPDATE`.
