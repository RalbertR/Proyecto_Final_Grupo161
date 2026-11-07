# 0010. Corrección de las actas devueltas

## Contexto

El destino puede devolver al origen un acta que no coincide con lo que llegó (HU-16). El origen la corrige y la reenvía, o desiste. Mientras tanto los bienes siguen bloqueados (RN-15).

La regla de las correcciones es que nunca se modifica el registro original (RN-07, ADR 0007). Pero una corrección del acta puede cambiar también los bienes y la unidad de destino, y `rectificacion` solo guarda el número de acta, la fecha y la descripción, con un motivo obligatorio.

## Decisión

- El número de acta, la fecha y la descripción corregidos se guardan como una `rectificacion` nueva, con el motivo de la última devolución. `PUT /api/movimientos/{id}` no recibe motivo propio.
- Los bienes (`movimiento_bien`) y la unidad de destino se cambian en la fila, porque el acta todavía no se aplicó y no tienen versiones.
- Cada devolución queda en `recepcion`, con los bienes con novedad en `recepcion_novedad`. El desistimiento del origen es una recepción `RECHAZADO` con su usuario y su motivo.
- La unicidad de la resolución se garantiza con una columna calculada: `uq_recepcion_resuelta` admite varias devoluciones del mismo acta, pero una sola recepción definitiva.

## Consecuencias

- Los bienes y el destino anteriores al reenvío no se conservan. Quedan las devoluciones, con su motivo y sus novedades, que dicen qué no coincidía.
- Si se cambia el destino, la unidad anterior deja de ver el acta.
- Una fecha del hecho corregida se valida contra hoy, como en la entrega.
