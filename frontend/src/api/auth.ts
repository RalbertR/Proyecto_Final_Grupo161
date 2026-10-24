import type { RespuestaLogin, Usuario } from "../tipos/usuario"
import { http } from "./http"

type Credenciales = { usuario: string; contrasena: string }

// OAuth2 Password Flow: el body va como formulario, no como JSON.
export const iniciarSesion = ({ usuario, contrasena }: Credenciales) =>
  http<RespuestaLogin>("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: usuario, password: contrasena }),
  })

export const obtenerYo = () => http<Usuario>("/api/auth/me")
