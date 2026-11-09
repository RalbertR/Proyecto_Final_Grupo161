export interface Documento {
  id: number
  nombre_original: string
  tipo_mime: string
  tamano_bytes: number
  hash_sha256: string
  usuario: string
  fecha_carga: string
}

export interface DocumentosDelActa {
  documentos: Documento[]
  puede_adjuntar: boolean
}

export const descargarPdf = (contenido: Blob, nombre: string) => {
  const url = URL.createObjectURL(contenido)
  const enlace = document.createElement("a")
  enlace.href = url
  enlace.download = nombre
  document.body.append(enlace)
  enlace.click()
  enlace.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}
