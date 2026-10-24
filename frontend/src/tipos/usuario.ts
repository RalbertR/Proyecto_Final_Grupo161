import type { Unidad } from "./unidad"

export interface Usuario {
  id: number
  nombre_usuario: string
  unidad: Unidad
}

export interface RespuestaLogin {
  access_token: string
  token_type: "bearer"
  usuario: Usuario
}
