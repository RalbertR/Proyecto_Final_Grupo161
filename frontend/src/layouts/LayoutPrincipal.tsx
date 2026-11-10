import { useQueryClient } from "@tanstack/react-query"
import type { ReactNode } from "react"
import { NavLink, Outlet, useNavigate } from "react-router-dom"
import { Boton } from "../componentes/Boton"
import { Escudo } from "../componentes/Escudo"
import { usePendientes } from "../estado/pendientes"
import { useSesion } from "../estado/sesion"
import type { NivelUnidad } from "../tipos/unidad"

const rolDelNivel: Record<NivelUnidad, string> = {
  DIRECCION: "Logístico de Dirección",
  REGIONAL: "Logístico Regional",
  OPERACIONAL: "Auxiliar Logístico",
}

const claseEnlace = ({ isActive }: { isActive: boolean }) =>
  `flex min-h-10 items-center justify-between gap-3 rounded-xs px-2.5 whitespace-nowrap focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-foco ${isActive ? "bg-marca-hover font-semibold text-white" : "text-gray-300 hover:bg-white/10 hover:text-white"}`

const Enlace = ({
  a,
  fin,
  cantidad,
  children,
}: {
  a: string
  fin?: boolean
  cantidad?: number
  children: ReactNode
}) => (
  <li>
    <NavLink to={a} end={fin} className={claseEnlace}>
      {children}
      {!!cantidad && (
        <span className="rounded-xs bg-pendiente px-1.5 font-mono text-xs font-medium text-marca">
          {cantidad}
        </span>
      )}
    </NavLink>
  </li>
)

export const LayoutPrincipal = () => {
  const { yo, porRecibir, devueltas, observados, cambiosObservados, aRevisar, corrige, revisa } =
    usePendientes()
  const cantidadObservados = (observados?.length ?? 0) + (cambiosObservados?.length ?? 0)
  const cerrar = useSesion((s) => s.cerrar)
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const handleCerrarSesion = () => {
    cerrar()
    queryClient.clear()
    navigate("/login", { replace: true })
  }

  return (
    <div className="min-h-screen bg-fondo text-gray-900 md:grid md:grid-cols-[232px_minmax(0,1fr)]">
      <nav
        aria-label="Principal"
        className="flex flex-wrap items-start gap-x-4 gap-y-3 bg-marca px-4 py-3 text-sm text-gray-300 md:sticky md:top-0 md:h-screen md:flex-col md:flex-nowrap md:items-stretch md:gap-6 md:py-5"
      >
        <div className="order-1 flex grow flex-col gap-3 md:grow-0">
          <span className="flex items-center gap-2.5 text-base font-semibold text-white">
            <Escudo className="size-5 shrink-0" />
            Sistema Logístico Policial
          </span>
          {yo && (
            <div className="flex flex-col gap-0.5">
              <span className="hidden font-etiqueta text-xs font-semibold tracking-wider text-gray-400 uppercase md:block">
                {rolDelNivel[yo.unidad.nivel]}
              </span>
              <span className="font-semibold text-white">{yo.unidad.nombre}</span>
            </div>
          )}
        </div>
        <ul className="order-3 -mx-1 flex w-full gap-1 overflow-x-auto px-1 [scrollbar-width:none] md:order-2 md:mx-0 md:flex-col md:overflow-visible md:px-0">
          <Enlace a="/" fin>
            Inicio
          </Enlace>
          <Enlace a="/inventario">Inventario</Enlace>
          <Enlace a="/por-recibir" cantidad={porRecibir?.length}>
            Por recibir
          </Enlace>
          <Enlace a="/devueltas" cantidad={devueltas?.length}>
            Devueltas
          </Enlace>
          {corrige && (
            <Enlace a="/observados" cantidad={cantidadObservados}>
              Observados
            </Enlace>
          )}
          {revisa && (
            <Enlace a="/revision" cantidad={aRevisar?.length}>
              Revisión
            </Enlace>
          )}
        </ul>
        <div className="order-2 flex items-center gap-3 md:order-3 md:mt-auto md:flex-col md:items-stretch md:gap-2 md:border-t md:border-white/15 md:pt-4">
          {yo && (
            <span
              title={yo.nombre_usuario}
              className="hidden truncate font-mono text-gray-400 md:block"
            >
              {yo.nombre_usuario}
            </span>
          )}
          <Boton variant="contorno" onClick={handleCerrarSesion} className="px-3 py-1.5 text-sm">
            Salir
          </Boton>
        </div>
      </nav>
      <main className="min-w-0 px-4 py-6 md:px-8 md:py-8">
        <div className="mx-auto max-w-7xl">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
