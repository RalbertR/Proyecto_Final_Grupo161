// Fila de GET /api/inventario
export interface FilaInventario {
  unidad_id: number
  unidad: string
  bien_id: number
  tipo_bien: string
  identificacion: string
  marca: string
  modelo: string
  estado_operativo: "EN_SERVICIO" | "FUERA_DE_SERVICIO"
  tenencia: "DEPOSITO" | "DOTACION"
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

export const areasDe = (bienes: FilaInventario[]) => [
  ...new Set(bienes.map((b) => areaDelTipo[b.tipo_bien])),
]

export const motivoBloqueo = (bien: FilaInventario, unidadPropiaId?: number) => {
  if (bien.unidad_id !== unidadPropiaId) return "Es de otra unidad"
  if (bien.tenencia === "DOTACION") return "Asignado a un oficial"
  if (bien.con_movimiento_pendiente) return "Tiene un movimiento pendiente"
  return null
}
