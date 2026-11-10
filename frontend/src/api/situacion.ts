import type { Situacion } from "../tipos/situacion"
import { http } from "./http"

export const obtenerSituacion = (regionalId?: number) =>
  http<Situacion>(regionalId ? `/api/situacion?regional_id=${regionalId}` : "/api/situacion")
