import type { EstadoOperativo } from "./bien"
import type { Revision } from "./movimiento"
import type { EventoActa } from "./revision"

export interface BienDelCambio {
  id: number
  identificacion: string
  tipo_bien: string
  marca: string
  modelo: string
}

export interface InformeCambio {
  id: number
  nombre_original: string
  tamano_bytes: number
}

export interface RectificacionCambio {
  version: number
  motivo: string
  usuario: string
  fecha: string
}

export interface CambioEstado {
  id: number
  bien: BienDelCambio
  estado_anterior: EstadoOperativo
  estado_nuevo: EstadoOperativo
  observaciones: string
  informe: InformeCambio | null
  estado: string
  estado_revision: string
  version_vigente: number
  unidad_registrante: string
  usuario: string
  fecha: string
  revisiones: Revision[]
  rectificaciones: RectificacionCambio[]
}

export interface RectificacionCambioCreate {
  version: number
  observaciones: string
  motivo: string
  informe: File | null
  quitarInforme: boolean
}

export const estadoOpuesto = (estado: EstadoOperativo): EstadoOperativo =>
  estado === "EN_SERVICIO" ? "FUERA_DE_SERVICIO" : "EN_SERVICIO"

export const ultimaObservacionCambio = (cambio: CambioEstado) =>
  cambio.revisiones.filter((revision) => revision.resultado === "OBSERVADO").at(-1)

export const historialCambio = (cambio: CambioEstado): EventoActa[] =>
  [
    ...cambio.revisiones.map((r): EventoActa => ({
      accion: r.resultado === "OBSERVADO" ? "Observado" : "Confirmado",
      usuario: r.usuario,
      fecha: r.fecha,
      motivo: r.motivo_observacion,
    })),
    ...cambio.rectificaciones.map((r): EventoActa => ({
      accion: "Corregido",
      usuario: r.usuario,
      fecha: r.fecha,
      motivo: r.motivo,
    })),
  ].sort((a, b) => a.fecha.localeCompare(b.fecha))
