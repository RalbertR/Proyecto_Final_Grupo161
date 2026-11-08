import type { Oficial } from "../tipos/movimiento"
import { http } from "./http"

export const obtenerOficiales = () => http<Oficial[]>("/api/oficiales")
