export type NivelUnidad = "DIRECCION" | "REGIONAL" | "OPERACIONAL"

export interface Unidad {
  id: number
  nombre: string
  nivel: NivelUnidad
}

export interface Ubicacion {
  id: number
  nombre: string
}
