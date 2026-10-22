import { useQuery } from "@tanstack/react-query"
import { Outlet } from "react-router-dom"
import { obtenerYo } from "../api/auth"

export const LayoutPrincipal = () => {
  const { data: yo } = useQuery({ queryKey: ["yo"], queryFn: obtenerYo, retry: false })

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
        <h1 className="text-2xl leading-tight font-semibold tracking-tight text-marca">
          Sistema Logístico Policial
        </h1>
        {yo && (
          <p className="text-sm text-secundario">
            <span className="font-semibold">{yo.nombre_usuario}</span> · {yo.unidad.nombre}
          </p>
        )}
      </header>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
