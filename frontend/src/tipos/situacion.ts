import type { NivelUnidad } from "./unidad"

export type Etapa = "POR_RECIBIR" | "EN_REVISION" | "OBSERVADA" | "DEVUELTA"

export interface TipoSituacion {
  tipo_bien: string
  total: number
  fuera_de_servicio: number
}

export interface UnidadSituacion {
  id: number
  nombre: string
  nivel: NivelUnidad
  tipos: TipoSituacion[]
  abiertas: number
}

export interface GrupoSituacion {
  etapa: Etapa
  cantidad: number
  dias_mas_antigua: number | null
}

export interface ActaDemorada {
  movimiento_id: number
  numero_acta: string | null
  etapa: Etapa
  unidad_id: number
  unidad: string
  dias: number
}

export interface Situacion {
  unidades: UnidadSituacion[]
  grupos: GrupoSituacion[]
  demoradas: ActaDemorada[]
}

export const nombreEtapa: Record<Etapa, string> = {
  POR_RECIBIR: "Por recibir",
  EN_REVISION: "En revisión",
  OBSERVADA: "Observadas",
  DEVUELTA: "Devueltas",
}

export const etapaDelActa: Record<Etapa, string> = {
  POR_RECIBIR: "Por recibir",
  EN_REVISION: "En revisión",
  OBSERVADA: "Observada",
  DEVUELTA: "Devuelta",
}

export const nombreTipoCorto: Record<string, string> = {
  ARMAMENTO: "Armamento",
  CHALECO: "Chalecos",
  MOVIL: "Móviles",
  EQUIPO_COMUNICACIONES: "Comunic.",
}

export const textoDias = (dias: number) => (dias === 1 ? "1 día" : `${dias} días`)

export const fraseSituacion = (grupos: GrupoSituacion[]) => {
  const total = grupos.reduce((suma, g) => suma + g.cantidad, 0)
  const mayor = Math.max(0, ...grupos.map((g) => g.dias_mas_antigua ?? 0))
  if (total === 0) return "No hay actas abiertas"
  if (total === 1)
    return mayor === 0 ? "Un acta abierta, de hoy" : `Un acta abierta, lleva ${textoDias(mayor)}`
  return mayor === 0
    ? `${total} actas abiertas, todas de hoy`
    : `${total} actas abiertas, la más demorada lleva ${textoDias(mayor)}`
}

export const antiguedad = (g: GrupoSituacion) => {
  if (g.cantidad === 0 || g.dias_mas_antigua === null) return "Sin actas"
  if (g.dias_mas_antigua === 0) return "Desde hoy"
  return `La más antigua, ${textoDias(g.dias_mas_antigua)}`
}

export const intensidad = (total: number, fuera: number) =>
  total === 0 ? 0 : Math.min(fuera / total / 0.5, 1)
