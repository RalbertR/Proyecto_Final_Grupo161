import type { Usuario } from "../tipos/usuario"
import { http } from "./http"

export const obtenerYo = () => http<Usuario>("/api/auth/me")
