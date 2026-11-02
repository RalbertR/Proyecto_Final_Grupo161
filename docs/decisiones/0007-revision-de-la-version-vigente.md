# 7. Revisión de la versión vigente

Aceptada el 29/10/2026.

## Contexto

La Regional revisa lo que registran sus Operacionales y Dirección lo que registran las Regionales. Un registro observado se corrige con una versión nueva y vuelve a revisión. Para saber qué se observó y qué se aprobó hay que guardar qué versión vio el revisor, y una aprobación no puede quedar asociada a datos que se corrigieron después.

## Decisión

Cada revisión guarda en `version_revisada` la versión que vio el revisor: 0 para el registro original o el número de la rectificación. Un trigger rechaza la revisión si esa versión no es la vigente, que es la última rectificación o el original si no hay ninguna. Vale para movimientos y para cambios de estado.

## Consecuencias

Si el autor corrige el registro mientras el revisor lo tiene abierto, la revisión se rechaza y la API responde 409 con el mensaje del trigger, igual que con los demás triggers.

Para que una revisión y una corrección simultáneas no se crucen, los triggers de `revision`, `rectificacion` y `rectificacion_cambio_estado` empiezan bloqueando la cabecera del registro con `SELECT ... FOR UPDATE`. Así la segunda operación espera a que la primera confirme y trabaja con lo que quedó, aunque usemos READ COMMITTED como dice el ADR 0001, y las dos operaciones no terminan en un deadlock cuando actualizan el estado de revisión de la cabecera.

Los triggers solos no alcanzan, así que la API también bloquea la cabecera con `FOR UPDATE` antes de leerla, tanto al revisar como al corregir. El trigger de `revision` controla la versión pero no el estado de revisión, y sin el bloqueo de la API dos revisiones simultáneas de la misma versión quedarían guardadas. Al corregir, el `INSERT ... SELECT` calcula el número de la versión nueva antes de que el trigger de `rectificacion` llegue a bloquear, y sin el bloqueo de la API la segunda corrección choca con `uq_rectificacion_version` y responde 500.
