import { Navigate, Outlet } from "react-router-dom"
import { useSesion } from "../estado/sesion"

export const RutaProtegida = () => {
  const token = useSesion((s) => s.token)
  return token ? <Outlet /> : <Navigate to="/login" replace />
}
