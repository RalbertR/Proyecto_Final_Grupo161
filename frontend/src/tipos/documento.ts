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
