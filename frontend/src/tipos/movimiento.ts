import { tiposDeBien } from "./bien"
import type { Ubicacion, Unidad } from "./unidad"

export interface EntregaCreate {
  unidad_destino_id: number
  numero_acta: string
  fecha_hecho: string
  descripcion: string | null
  bienes: number[]
}

export interface RenglonMovimiento {
  bien_id: number
  tipo_bien: string
  identificacion: string
  marca: string
  modelo: string
  estado_operativo: string
  ubicacion_origen: string | null
  ubicacion_destino: string | null
}

export interface Movimiento {
  id: number
  tipo: string
  estado: string
  estado_revision: string
  numero_acta: string | null
  fecha_hecho: string
  descripcion: string | null
  unidad_origen: Unidad | null
  unidad_destino: Unidad | null
  usuario: string
  fecha_carga: string
  bienes: RenglonMovimiento[]
}

export type Recepcion =
  | { resultado: "ACEPTADO"; ubicaciones: { bien_id: number; ubicacion_id: number }[] }
  | { resultado: "RECHAZADO"; motivo_rechazo: string }

export interface ControlBien {
  controlado: boolean
  conNovedad: boolean
  ubicacionId?: number
}

export type ControlActa = Record<number, ControlBien>

export const fechaLegible = (fecha: string) => fecha.split("-").reverse().join("/")

export const cambiarControl = (
  actual: ControlBien | undefined,
  cambio: Partial<ControlBien>,
): ControlBien => {
  const nuevo = { controlado: false, conNovedad: false, ...actual, ...cambio }
  if (cambio.conNovedad) nuevo.controlado = true
  if (cambio.controlado === false) nuevo.conNovedad = false
  return nuevo
}

const ubicacionDelTipo: Record<string, string> = {
  ARMAMENTO: "Sala de Armas",
  CHALECO: "Sala de Armas",
  EQUIPO_COMUNICACIONES: "Depósito",
  MOVIL: "Playón",
}

const normalizar = (texto: string) => texto.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase()

export const ubicacionPorDefecto = (tipoBien: string, ubicaciones: Ubicacion[]) => {
  const nombre = ubicacionDelTipo[tipoBien]
  if (!nombre) return undefined
  return ubicaciones.find((u) => normalizar(u.nombre) === normalizar(nombre))?.id
}

export const motivoInicial = (bienes: RenglonMovimiento[], control: ControlActa) => {
  const conNovedad = bienes.filter((b) => control[b.bien_id]?.conNovedad)
  if (conNovedad.length === 0) return ""
  const lista = conNovedad
    .map((b) => `${tiposDeBien[b.tipo_bien] ?? b.tipo_bien} ${b.identificacion}`)
    .join(", ")
  return `Con novedad: ${lista}. `.slice(0, 500)
}
