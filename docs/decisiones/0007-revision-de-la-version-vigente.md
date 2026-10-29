# 7. Revisión de la versión vigente

Aceptada el 29/10/2026.

## Contexto

La Regional revisa lo que registran sus Operacionales y Dirección lo que registran las Regionales. Un registro observado se corrige con una versión nueva y vuelve a revisión. Para saber qué se observó y qué se aprobó hay que guardar qué versión vio el revisor, y una aprobación no puede quedar asociada a datos que se corrigieron después.

## Decisión

Cada revisión guarda en `version_revisada` la versión que vio el revisor: 0 para el registro original o el número de la rectificación. Un trigger rechaza la revisión si esa versión no es la vigente, que es la última rectificación o el original si no hay ninguna. Vale para movimientos y para cambios de estado.

## Consecuencias

Si el autor corrige el registro mientras el revisor lo tiene abierto, la revisión se rechaza y la API responde 409 con el mensaje del trigger, igual que con los demás triggers.

Trabajamos con READ COMMITTED, como dice el ADR 0001, así que el trigger no ve una rectificación que todavía no se confirmó. Para que una revisión y una corrección simultáneas no pasen las dos, la API de revisión y la de rectificación bloquean la cabecera del registro con `SELECT ... FOR UPDATE` antes de escribir.
