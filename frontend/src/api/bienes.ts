import type { HistorialBien } from "../tipos/historial"
import { http } from "./http"

export const obtenerHistorial = (bienId: number) =>
  http<HistorialBien>(`/api/bienes/${bienId}/historial`)
