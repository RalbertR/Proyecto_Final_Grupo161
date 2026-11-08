import type {
  DevolucionCreate,
  EntregaCreate,
  Movimiento,
  Recepcion,
  RectificacionCreate,
} from "../tipos/movimiento"
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

export const obtenerMovimiento = (id: number) => http<Movimiento>(`/api/movimientos/${id}`)

export const obtenerObservados = () => http<Movimiento[]>("/api/movimientos/observados")

export const obtenerDevueltas = () => http<Movimiento[]>("/api/movimientos/devueltas")

export const corregirEntrega = (id: number, entrega: EntregaCreate) =>
  http<Movimiento>(`/api/movimientos/${id}`, {
    method: "PUT",
    body: JSON.stringify(entrega),
  })

export const desistirDeLaEntrega = (id: number, motivo: string) =>
  http<Movimiento>(`/api/movimientos/${id}/desistimiento`, {
    method: "POST",
    body: JSON.stringify({ motivo }),
  })

export const rectificarMovimiento = (id: number, rectificacion: RectificacionCreate) =>
  http<Movimiento>(`/api/movimientos/${id}/rectificaciones`, {
    method: "POST",
    body: JSON.stringify(rectificacion),
  })

export const registrarDevolucion = (devolucion: DevolucionCreate) =>
  http<Movimiento>("/api/movimientos/devoluciones", {
    method: "POST",
    body: JSON.stringify(devolucion),
  })
