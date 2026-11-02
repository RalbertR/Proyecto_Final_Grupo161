import type { Revision } from "../tipos/movimiento"
import type { RegistroBandeja, RevisionCreate } from "../tipos/revision"
import { http } from "./http"

export const obtenerMovimientosARevisar = async () => {
  const bandeja = await http<RegistroBandeja[]>("/api/revisiones/bandeja")
  return bandeja.filter((registro) => registro.registro === "MOVIMIENTO")
}

export const revisarMovimiento = (id: number, revision: RevisionCreate) =>
  http<Revision>(`/api/movimientos/${id}/revisiones`, {
    method: "POST",
    body: JSON.stringify(revision),
  })
