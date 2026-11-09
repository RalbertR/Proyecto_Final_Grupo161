import type { EstadoOperativo } from "../tipos/bien"
import type { CambioEstado, RectificacionCambioCreate } from "../tipos/cambioEstado"
import type { Revision } from "../tipos/movimiento"
import type { RevisionCreate } from "../tipos/revision"
import { http, httpBlob } from "./http"

const sumarPdf = (formulario: FormData, archivo: File | null) => {
  if (!archivo) return
  const contenido = archivo.type ? archivo : new Blob([archivo], { type: "application/pdf" })
  formulario.append("informe", contenido, archivo.name)
}

export const registrarCambio = (
  bienId: number,
  estadoNuevo: EstadoOperativo,
  observaciones: string,
  informe: File | null,
) => {
  const formulario = new FormData()
  formulario.append("estado_nuevo", estadoNuevo)
  formulario.append("observaciones", observaciones)
  sumarPdf(formulario, informe)
  return http<CambioEstado>(`/api/bienes/${bienId}/cambios-estado`, {
    method: "POST",
    body: formulario,
  })
}

export const obtenerCambio = (id: number) => http<CambioEstado>(`/api/cambios-estado/${id}`)

export const obtenerInforme = (id: number) => httpBlob(`/api/cambios-estado/${id}/informe`)

export const obtenerCambiosObservados = () => http<CambioEstado[]>("/api/cambios-estado/observados")

export const revisarCambio = (id: number, revision: RevisionCreate) =>
  http<Revision>(`/api/cambios-estado/${id}/revisiones`, {
    method: "POST",
    body: JSON.stringify(revision),
  })

export const rectificarCambio = (id: number, datos: RectificacionCambioCreate) => {
  const formulario = new FormData()
  formulario.append("version", String(datos.version))
  formulario.append("observaciones", datos.observaciones)
  formulario.append("motivo", datos.motivo)
  formulario.append("quitar_informe", String(datos.quitarInforme))
  sumarPdf(formulario, datos.informe)
  return http<CambioEstado>(`/api/cambios-estado/${id}/rectificaciones`, {
    method: "POST",
    body: formulario,
  })
}
