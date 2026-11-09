# HU-17. Cambios de estado de servicio

Contrato local de la [issue #68](https://github.com/RalbertR/Proyecto_Final_Grupo161/issues/68). Todos los pedidos requieren un token de sesión en `Authorization: Bearer <token>`.

Un cambio de estado no es un movimiento: no lleva acta y no cambia la unidad, la ubicación ni el oficial del bien. Los PDF se validan y se guardan igual que los documentos de las actas, descritos en [documentos.md](documentos.md).

## Registrar

`POST /api/bienes/{bien_id}/cambios-estado`

Recibe un formulario `multipart/form-data`:

| Campo | Contenido |
|---|---|
| `estado_nuevo` | `EN_SERVICIO` o `FUERA_DE_SERVICIO`. |
| `observaciones` | De 1 a 500 caracteres. Con el motivo, o con lo que se reparó. |
| `informe` | PDF. Obligatorio para pasar a fuera de servicio y opcional para volver a servicio. |

Solo lo registra la unidad dueña del bien. La API bloquea la fila del bien antes de validar, guarda el PDF, registra el cambio y actualiza el estado del bien en una sola transacción. Si algo falla, no queda ni el archivo ni el registro. Lo que registra Dirección queda con `estado_revision` `NO_APLICA` y el resto queda `PENDIENTE`.

Responde **201** con el cambio:

```json
{
  "id": 7,
  "bien": { "id": 141, "identificacion": "RD-0457", "tipo_bien": "EQUIPO_COMUNICACIONES", "marca": "Motorola", "modelo": "DEP450" },
  "estado_anterior": "EN_SERVICIO",
  "estado_nuevo": "FUERA_DE_SERVICIO",
  "observaciones": "No transmite. Se golpeó en un procedimiento.",
  "informe": { "id": 33, "nombre_original": "informe_RD-0457.pdf", "tamano_bytes": 182311 },
  "estado": "APLICADO",
  "estado_revision": "PENDIENTE",
  "version_vigente": 0,
  "unidad_registrante": "Unidad Operacional A",
  "usuario": "aux.unidad_a",
  "fecha": "2026-11-09T10:21:00",
  "revisiones": [],
  "rectificaciones": []
}
```

Las observaciones y el informe son los de la versión vigente.

## Consultar

`GET /api/cambios-estado/{cambio_id}` responde **200** con el mismo cuerpo.

`GET /api/cambios-estado/{cambio_id}/informe` descarga el PDF vigente con los mismos encabezados que los documentos de las actas.

Los ve un usuario que puede ver el historial del bien, o uno de la unidad que registró el cambio o de su superior inmediato.

## Revisar

`POST /api/cambios-estado/{cambio_id}/revisiones`, con el mismo cuerpo que la revisión de movimientos:

```json
{ "resultado": "OBSERVADO", "version": 0, "motivo_observacion": "El informe no está firmado" }
```

Solo revisa el superior inmediato de la unidad que lo registró, y solo un cambio aplicado y pendiente de revisión. `version` va de 0 a 65535 y tiene que ser la vigente. Responde **201** con la revisión.

## Observados y corrección

`GET /api/cambios-estado/observados` responde **200** con los cambios observados que registró la unidad del usuario.

`POST /api/cambios-estado/{cambio_id}/rectificaciones` recibe un formulario `multipart/form-data`:

| Campo | Contenido |
|---|---|
| `version` | La versión vigente que vio el usuario. |
| `observaciones` | De 1 a 500 caracteres. |
| `motivo` | De 1 a 500 caracteres. |
| `informe` | PDF nuevo, opcional. Sin archivo se conserva el informe vigente. |
| `quitar_informe` | `true` para quitar el informe de una vuelta a servicio. No se combina con un archivo nuevo. |

Solo corrige la unidad que registró el cambio, y solo uno observado. La corrección se guarda como una versión nueva, el cambio vuelve a quedar pendiente de revisión y el estado del bien no cambia. Responde **201** con el cambio actualizado.

## Errores

| Estado | Motivo |
|---|---|
| 401 | Falta una sesión válida. |
| 403 | El bien es de otra unidad, el usuario no puede ver el cambio, no es el superior que revisa o no es de la unidad que lo registró. |
| 404 | No existe el bien, el cambio o su informe. |
| 409 | El bien tiene un movimiento pendiente o devuelto, está de baja o ya está en ese estado. El cambio no está pendiente de revisión, no está observado o la versión no es la vigente. El PDF ya está cargado. |
| 422 | Faltan las observaciones o el motivo, o superan los 500 caracteres. Falta el informe para pasar a fuera de servicio, se intenta quitarlo de un fuera de servicio o el PDF no es válido. La versión está fuera de rango. |
| 503 | No se pudo guardar el PDF en el almacenamiento privado. Se puede volver a intentar. |
