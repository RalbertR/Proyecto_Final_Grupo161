import { useSesion } from "../estado/sesion"

export async function http<T>(url: string, init?: RequestInit): Promise<T> {
  const { token, cerrar } = useSesion.getState()
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  })
  if (res.status === 401 && token) {
    // Sesion vencida: recarga completa a /login
    cerrar()
    window.location.replace("/login")
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(typeof body?.detail === "string" ? body.detail : `Error ${res.status}`)
  }
  return res.status === 204 ? (undefined as T) : res.json()
}
