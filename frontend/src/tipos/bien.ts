import type { RenglonMovimiento } from "./movimiento"

export type EstadoOperativo = "EN_SERVICIO" | "FUERA_DE_SERVICIO"

export type Tenencia = "DEPOSITO" | "DOTACION"

export const nombreEstadoOperativo: Record<EstadoOperativo, string> = {
  EN_SERVICIO: "En servicio",
  FUERA_DE_SERVICIO: "Fuera de servicio",
}

// Fila de GET /api/inventario
export interface FilaInventario {
  unidad_id: number
  unidad: string
  bien_id: number
  tipo_bien: string
  identificacion: string
  marca: string
  modelo: string
  estado_operativo: EstadoOperativo
  tenencia: Tenencia
  ubicacion: string | null
  oficial_legajo: string | null
  oficial: string | null
  con_movimiento_pendiente: boolean
}

// Catalogo tipo_bien de la base
export const tiposDeBien: Record<string, string> = {
  ARMAMENTO: "Armamento",
  CHALECO: "Chaleco balístico",
  MOVIL: "Móvil",
  EQUIPO_COMUNICACIONES: "Equipo de comunicaciones",
}

export const areaDelTipo: Record<string, string> = {
  ARMAMENTO: "Armamento y chalecos",
  CHALECO: "Armamento y chalecos",
  MOVIL: "Móviles y equipos de comunicaciones",
  EQUIPO_COMUNICACIONES: "Móviles y equipos de comunicaciones",
}

export const areasDe = (bienes: Pick<FilaInventario, "tipo_bien">[]) => [
  ...new Set(bienes.map((b) => areaDelTipo[b.tipo_bien])),
]

export const motivoParaSumar = (
  bien: FilaInventario,
  unidadId: number,
  enLista: BienActa[],
  propios: Set<number>,
) => {
  const bloqueo = motivoBloqueo(bien, unidadId)
  if (bloqueo && !(bloqueo === "Tiene un movimiento pendiente" && propios.has(bien.bien_id)))
    return bloqueo
  const area = areasDe(enLista)[0]
  if (area && areaDelTipo[bien.tipo_bien] !== area) return "Es de otra área"
  return null
}

export type BienActa = Pick<
  FilaInventario,
  "bien_id" | "tipo_bien" | "identificacion" | "marca" | "modelo" | "ubicacion"
>

export const bienDelRenglon = (renglon: RenglonMovimiento): BienActa => ({
  bien_id: renglon.bien_id,
  tipo_bien: renglon.tipo_bien,
  identificacion: renglon.identificacion,
  marca: renglon.marca,
  modelo: renglon.modelo,
  ubicacion: renglon.ubicacion_origen,
})

export const motivoBloqueo = (bien: FilaInventario, unidadPropiaId?: number) => {
  if (bien.unidad_id !== unidadPropiaId) return "Es de otra unidad"
  if (bien.tenencia === "DOTACION") return "Asignado a un oficial"
  if (bien.con_movimiento_pendiente) return "Tiene un movimiento pendiente"
  return null
}
