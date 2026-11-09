import { useSesion } from "../estado/sesion"

export class ErrorHttp extends Error {
  status: number

  constructor(mensaje: string, status: number) {
    super(mensaje)
    this.status = status
  }
}

async function solicitar(url: string, init?: RequestInit): Promise<Response> {
  const { token, cerrar } = useSesion.getState()
  const headers = new Headers(init?.headers)
  if (!headers.has("Content-Type") && !(init?.body instanceof FormData))
    headers.set("Content-Type", "application/json")
  if (token && !headers.has("Authorization")) headers.set("Authorization", `Bearer ${token}`)
  const res = await fetch(url, {
    ...init,
    headers,
  })
  if (res.status === 401 && token) {
    // Sesion vencida: recarga completa a /login
    cerrar()
    window.location.replace("/login")
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ErrorHttp(
      typeof body?.detail === "string" ? body.detail : `Error ${res.status}`,
      res.status,
    )
  }
  return res
}

export async function http<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await solicitar(url, init)
  return res.status === 204 ? (undefined as T) : res.json()
}

export async function httpBlob(url: string, init?: RequestInit): Promise<Blob> {
  return (await solicitar(url, init)).blob()
}
