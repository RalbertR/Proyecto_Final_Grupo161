import type { Unidad } from "./unidad"

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
