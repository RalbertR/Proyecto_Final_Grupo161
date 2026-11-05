# 8. Actas anteriores de un bien

Aceptada el 4/11/2026.

## Contexto

El historial de un bien muestra todas sus actas, también las de antes de que llegara a la unidad que lo tiene hoy. `GET /api/movimientos/{id}` solo respondía a las unidades de origen y de destino del acta, así que esa unidad veía el número de acta en el historial pero no podía abrirla.

## Decisión

`GET /api/movimientos/{id}` también responde si el alcance del usuario incluye la unidad que hoy tiene alguno de los bienes del acta. La regla vale solo para consultar. Revisar y corregir siguen como estaban.

## Consecuencias

Quien abre un acta anterior la ve completa, con los otros bienes que figuran en ella aunque hoy sean de otra unidad. Se aceptó así porque un acta es un solo documento y recortarla mostraría algo distinto de lo que se firmó.

El acceso depende de quién tiene el bien hoy. Cuando el bien pasa a otra unidad, la anterior deja de abrir las actas en las que no figura como origen ni destino.
