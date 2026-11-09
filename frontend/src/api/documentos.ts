import type { Documento, DocumentosDelActa } from "../tipos/documento"
import { http, httpBlob } from "./http"

const ruta = (movimientoId: number) => `/api/movimientos/${movimientoId}/documentos`

export const obtenerDocumentos = (movimientoId: number) =>
  http<DocumentosDelActa>(ruta(movimientoId))

export const adjuntarDocumento = (movimientoId: number, archivo: File) => {
  const formulario = new FormData()
  const contenido = archivo.type ? archivo : new Blob([archivo], { type: "application/pdf" })
  formulario.append("archivo", contenido, archivo.name)
  return http<Documento>(ruta(movimientoId), { method: "POST", body: formulario })
}

export const obtenerArchivoDocumento = (movimientoId: number, documentoId: number) =>
  httpBlob(`${ruta(movimientoId)}/${documentoId}`)
