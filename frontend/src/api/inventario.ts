import type { FilaInventario } from "../tipos/bien"
import { http } from "./http"

export const obtenerInventario = (unidadId?: number) =>
  http<FilaInventario[]>(unidadId ? `/api/inventario?unidad_id=${unidadId}` : "/api/inventario")
