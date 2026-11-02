import type { RegistroBandeja } from "../tipos/revision"
import { http } from "./http"

export const obtenerMovimientosARevisar = async () => {
  const bandeja = await http<RegistroBandeja[]>("/api/revisiones/bandeja")
  return bandeja.filter((registro) => registro.registro === "MOVIMIENTO")
}
