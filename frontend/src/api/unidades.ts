import type { Ubicacion, Unidad } from "../tipos/unidad"
import { http } from "./http"

export const obtenerUnidades = () => http<Unidad[]>("/api/unidades")

export const obtenerDestinos = () => http<Unidad[]>("/api/unidades/destinos")

export const obtenerUbicaciones = () => http<Ubicacion[]>("/api/ubicaciones")
