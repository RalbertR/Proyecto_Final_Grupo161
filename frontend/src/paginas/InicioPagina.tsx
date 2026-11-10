import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { obtenerInventario } from "../api/inventario"
import { Boton } from "../componentes/Boton"
import { claseBoton } from "../componentes/claseBoton"
import { ListaPendientes } from "../componentes/ListaPendientes"
import { TarjetasInventario } from "../componentes/TarjetasInventario"
import { usePendientes } from "../estado/pendientes"
import {
  armarPendientes,
  fechaDeHoyEnLetras,
  resumenPorTipo,
  tituloInicio,
} from "../tipos/pendiente"

export const InicioPagina = () => {
  const { yo, cargando, error, reintentar, ...fuentes } = usePendientes()
  const unidadId = yo?.unidad.id
  const inventario = useQuery({
    queryKey: ["inventario", unidadId],
    queryFn: () => obtenerInventario(unidadId),
    enabled: unidadId !== undefined,
    retry: false,
  })
  const pendientes = armarPendientes(fuentes)

  if (!yo || cargando || inventario.isLoading)
    return (
      <div aria-busy="true" className="space-y-3">
        <div className="h-16 animate-pulse rounded-xs bg-gray-200" />
        <div className="h-28 animate-pulse rounded-xs bg-gray-200" />
        <div className="h-64 animate-pulse rounded-xs bg-gray-200" />
      </div>
    )

  return (
    <section className="flex flex-col gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <p className="font-etiqueta text-sm font-semibold tracking-wider text-gray-500 uppercase">
            {fechaDeHoyEnLetras(new Date())}
          </p>
          <h1 className="text-2xl leading-tight font-semibold tracking-tight">
            {error ? "No se pudo cargar lo pendiente" : tituloInicio(pendientes.length)}
          </h1>
        </div>
        <Link to="/entregas/nueva" className={claseBoton()}>
          Nueva entrega
        </Link>
      </header>
      {inventario.isError ? (
        <p role="alert" className="rounded-xs border border-error bg-white p-4 text-error">
          {inventario.error.message}
        </p>
      ) : (
        <TarjetasInventario resumen={resumenPorTipo(inventario.data ?? [])} />
      )}
      {error ? (
        <div
          role="alert"
          className="flex flex-wrap items-center justify-between gap-3 rounded-xs border border-error bg-white px-4 py-3 text-error"
        >
          <span>No se pudo cargar lo pendiente: {error.message}</span>
          <Boton variant="contorno" onClick={reintentar} className="px-3 py-1.5 text-sm">
            Reintentar
          </Boton>
        </div>
      ) : (
        <ListaPendientes pendientes={pendientes} />
      )}
    </section>
  )
}
