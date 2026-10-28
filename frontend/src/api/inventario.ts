import type { FilaInventario } from "../tipos/bien"
import { http } from "./http"

export const obtenerInventario = () => http<FilaInventario[]>("/api/inventario")
