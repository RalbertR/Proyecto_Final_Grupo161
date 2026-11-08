# HU-13. Documentos de las actas

Contrato local de la [issue #45](https://github.com/RalbertR/Proyecto_Final_Grupo161/issues/45). Todos los pedidos requieren un token de sesión en `Authorization: Bearer <token>`.

## Adjuntar

`POST /api/movimientos/{movimiento_id}/documentos`

Recibe un formulario `multipart/form-data` con un archivo en el campo `archivo`. El movimiento debe estar registrado. Solo puede adjuntar un usuario de la unidad que lo registró, aunque lo haya cargado otra persona de esa unidad.

El archivo debe tener extensión `.pdf`, tipo `application/pdf` y contenido PDF válido. El límite es de 10 MiB (10.485.760 bytes), incluido el límite exacto. No alcanza con cambiar el nombre o el tipo de un archivo de texto. Un PDF cifrado que no se pueda validar sin contraseña se rechaza.

Responde **201** con los metadatos del documento:

```json
{
  "id": 1,
  "nombre_original": "acta-firmada.pdf",
  "tipo_mime": "application/pdf",
  "tamano_bytes": 25480,
  "hash_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "usuario": "aux.unidad_a",
  "fecha_carga": "2026-11-08T12:00:00"
}
```

El nombre original se conserva como nombre de descarga, sin las carpetas enviadas por el cliente. La ruta privada y el nombre generado para almacenar el archivo no se exponen en la API. La fecha y el usuario se toman del servidor y de la sesión.

Un movimiento puede tener varios PDFs distintos, como permite `movimiento_documento`. El hash SHA-256 es único en toda la tabla `documento`: volver a cargar el mismo contenido responde **409**, también si se envía con otro nombre o para otra acta. El rechazo no modifica el adjunto existente. Esta versión no permite reemplazar ni borrar documentos.

## Listar

`GET /api/movimientos/{movimiento_id}/documentos`

Responde **200** con:

```json
{
  "documentos": [],
  "puede_adjuntar": true
}
```

Cada elemento de `documentos` tiene los metadatos de la respuesta de carga. Sin adjuntos la lista está vacía. `puede_adjuntar` indica si el usuario pertenece a la unidad registrante; la API vuelve a comprobar ese permiso al cargar.

## Descargar

`GET /api/movimientos/{movimiento_id}/documentos/{documento_id}`

Responde **200** con los bytes originales, `Content-Type: application/pdf` y `Content-Disposition: attachment` con el nombre original saneado. El documento debe estar asociado al movimiento de la URL.

Listar y descargar usan los mismos permisos que `GET /api/movimientos/{id}`. Incluyen a las unidades de origen y destino, sus superiores y la unidad que hoy tiene algún bien del acta, según el [ADR 0008](../decisiones/0008-actas-anteriores-de-un-bien.md). Ese acceso de consulta no habilita a adjuntar.

## Errores

| Estado | Motivo |
|---|---|
| 401 | Falta una sesión válida. |
| 403 | El usuario no puede consultar el acta, o intenta adjuntar desde otra unidad. |
| 404 | El movimiento no existe, el documento solicitado no está asociado a él o su archivo físico no está disponible. |
| 409 | Ya existe un documento con el mismo SHA-256. |
| 422 | Falta el archivo, no es un PDF válido, supera el límite o su nombre no es válido. |
| 503 | No se pudo guardar el archivo en el almacenamiento privado; se puede volver a intentar. |

Una carga rechazada no deja un documento ni un archivo nuevo. La asociación al movimiento y los metadatos se guardan en una transacción. El índice único de hash también resuelve las cargas simultáneas del mismo PDF.

## Almacenamiento

En desarrollo se usa `backend/archivos_privados/documentos`, ignorado por Git. Se puede cambiar con `DIRECTORIO_DOCUMENTOS` en el `.env`; vacío conserva el valor por defecto. En producción el backend usa el volumen `documentos_privados`, que nginx no monta ni sirve. Los archivos tienen nombres generados y solo se descargan a través de la API autenticada.

Se reutilizan las tablas `documento` y `movimiento_documento` del esquema inicial, sin migraciones nuevas.
