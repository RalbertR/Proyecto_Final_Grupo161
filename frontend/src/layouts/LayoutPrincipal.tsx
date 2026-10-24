import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Outlet, useNavigate } from "react-router-dom"
import { obtenerYo } from "../api/auth"
import { Boton } from "../componentes/Boton"
import { Escudo } from "../componentes/Escudo"
import { useSesion } from "../estado/sesion"
import type { NivelUnidad } from "../tipos/unidad"

const nombreNivel: Record<NivelUnidad, string> = {
  DIRECCION: "Dirección",
  REGIONAL: "Regional",
  OPERACIONAL: "Operacional",
}

export const LayoutPrincipal = () => {
  const { data: yo } = useQuery({ queryKey: ["yo"], queryFn: obtenerYo, retry: false })
  const cerrar = useSesion((s) => s.cerrar)
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const handleCerrarSesion = () => {
    cerrar()
    queryClient.clear()
    navigate("/login", { replace: true })
  }

  return (
    <div className="min-h-screen bg-white text-gray-900">
      <header className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 bg-marca px-6 py-3 text-gray-50">
        <span className="flex items-center gap-2.5 font-semibold">
          <Escudo className="size-5" />
          Sistema Logístico Policial
        </span>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
          {yo && (
            <>
              <span className="font-mono text-xs tracking-widest text-gray-400 uppercase">
                {nombreNivel[yo.unidad.nivel]}
              </span>
              <span className="font-semibold">{yo.unidad.nombre}</span>
              <span className="font-mono text-gray-300">{yo.nombre_usuario}</span>
            </>
          )}
          <Boton variant="contorno" onClick={handleCerrarSesion} className="px-3 py-1.5 text-sm">
            Cerrar sesión
          </Boton>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  )
}
