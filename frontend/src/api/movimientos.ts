import type { EntregaCreate, Movimiento } from "../tipos/movimiento"
import { http } from "./http"

export const registrarEntrega = (entrega: EntregaCreate) =>
  http<Movimiento>("/api/movimientos/entregas", {
    method: "POST",
    body: JSON.stringify(entrega),
  })

export const obtenerPorRecibir = () => http<Movimiento[]>("/api/movimientos/por-recibir")
