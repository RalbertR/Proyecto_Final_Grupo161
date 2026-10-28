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
