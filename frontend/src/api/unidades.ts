import type { Unidad } from "../tipos/unidad"
import { http } from "./http"

export const obtenerUnidades = () => http<Unidad[]>("/api/unidades")
