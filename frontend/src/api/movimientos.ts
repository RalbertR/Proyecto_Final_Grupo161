import type { EntregaCreate, Movimiento, Recepcion } from "../tipos/movimiento"
import { http } from "./http"

export const registrarEntrega = (entrega: EntregaCreate) =>
  http<Movimiento>("/api/movimientos/entregas", {
    method: "POST",
    body: JSON.stringify(entrega),
  })

export const obtenerPorRecibir = () => http<Movimiento[]>("/api/movimientos/por-recibir")

export const recibirEntrega = (id: number, recepcion: Recepcion) =>
  http<Movimiento>(`/api/movimientos/${id}/recepcion`, {
    method: "POST",
    body: JSON.stringify(recepcion),
  })
