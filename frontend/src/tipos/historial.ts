import type { Tono } from "../componentes/Marca"
import type { EstadoOperativo, Tenencia } from "./bien"

export interface BienHistorial {
  id: number
  tipo_bien: string
  identificacion: string
  marca: string
  modelo: string
  unidad: string
  estado_operativo: EstadoOperativo
  tenencia: Tenencia
  ubicacion: string | null
  oficial_legajo: string | null
  oficial: string | null
  con_movimiento_pendiente: boolean
}

export interface EventoHistorial {
  registro: "MOVIMIENTO" | "CAMBIO_ESTADO"
  registro_id: number
  orden: number | null
  evento: string
  fecha: string
  numero_acta: string | null
  estado: string | null
  estado_revision: string
  origen: string | null
  destino: string | null
  unidad_duena: string | null
  estado_operativo_nuevo: EstadoOperativo | null
  detalle: string | null
}

export interface HistorialBien {
  bien: BienHistorial
  eventos: EventoHistorial[]
}

type MarcaEvento = { texto: string; tono: Tono }

const marcaPorEstado: Record<string, MarcaEvento> = {
  PENDIENTE: { texto: "Pendiente de recepción", tono: "pendiente" },
  RECHAZADO: { texto: "Rechazado", tono: "error" },
  ANULADO: { texto: "Anulado", tono: "error" },
}

const marcaPorRevision: Record<string, MarcaEvento> = {
  NO_APLICA: { texto: "Aplicado", tono: "secundario" },
  PENDIENTE: { texto: "Pendiente de revisión", tono: "pendiente" },
  REVISADO: { texto: "Revisado", tono: "secundario" },
  OBSERVADO: { texto: "Observado", tono: "error" },
}

export const marcaEvento = (evento: EventoHistorial): MarcaEvento =>
  marcaPorEstado[evento.estado ?? ""] ?? marcaPorRevision[evento.estado_revision]
