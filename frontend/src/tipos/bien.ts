import type { Oficial, RenglonMovimiento } from "./movimiento"

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
  oficial_id: number | null
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

export const motivosDeBloqueo = (
  bienes: BienActa[],
  frescas: FilaInventario[],
  regla: (fresca: FilaInventario | undefined) => string | null,
) => {
  const motivos = new Map<number, string>()
  for (const bien of bienes) {
    const motivo = regla(frescas.find((f) => f.bien_id === bien.bien_id))
    if (motivo) motivos.set(bien.bien_id, motivo)
  }
  return motivos
}

export const motivoBloqueo = (bien: FilaInventario, unidadPropiaId?: number) => {
  if (bien.unidad_id !== unidadPropiaId) return "Es de otra unidad"
  if (bien.tenencia === "DOTACION") return "Asignado a un oficial"
  if (bien.con_movimiento_pendiente) return "Tiene un movimiento pendiente"
  return null
}

export const motivoSinTilde = (bien: FilaInventario, unidadPropiaId?: number) => {
  if (bien.unidad_id !== unidadPropiaId) return "Es de otra unidad"
  if (bien.con_movimiento_pendiente) return "Tiene un movimiento pendiente"
  return null
}

export const oficialesDe = (bienes: Pick<FilaInventario, "oficial_id">[]) => [
  ...new Set(bienes.flatMap((b) => (b.oficial_id === null ? [] : [b.oficial_id]))),
]

export const motivoParaDevolver = (fresca: FilaInventario | undefined, oficialId: number) => {
  if (!fresca) return "Ya no está en el inventario"
  if (fresca.con_movimiento_pendiente) return "Tiene un movimiento pendiente"
  if (fresca.oficial_id !== oficialId) return "Ya no está asignado a ese oficial"
  return null
}

export const tiposRepetidos = (bienes: Pick<FilaInventario, "tipo_bien">[]) =>
  new Set(bienes.map((b) => b.tipo_bien)).size < bienes.length

const articuloDelTipo: Record<string, string> = {
  ARMAMENTO: "un arma",
  CHALECO: "un chaleco",
  EQUIPO_COMUNICACIONES: "un equipo de comunicaciones",
  MOVIL: "un móvil",
}

export const textoTipos = (tipos: string[]) =>
  tipos.map((t) => articuloDelTipo[t] ?? t).join(" ni ")

const sinTildes = (texto: string) => texto.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase()

export const coincideOficial = (oficial: Oficial, texto: string) => {
  const buscado = sinTildes(texto.trim())
  return oficial.legajo.startsWith(buscado) || sinTildes(oficial.nombre).includes(buscado)
}

export const oficialesQueCumplen = (
  oficiales: Oficial[],
  inventario: FilaInventario[],
  tipos: string[],
) => {
  const ocupados = new Set(
    inventario.flatMap((b) =>
      b.oficial_id !== null && tipos.includes(b.tipo_bien) ? [b.oficial_id] : [],
    ),
  )
  return oficiales.filter((o) => !ocupados.has(o.id))
}
