import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { Navigate } from "react-router-dom"
import { obtenerYo } from "../api/auth"
import { obtenerObservados } from "../api/movimientos"
import { Boton } from "../componentes/Boton"
import { Marca } from "../componentes/Marca"
import { ModalRectificacion } from "../componentes/ModalRectificacion"
import { fechaLegible, ultimaObservacion, type Movimiento } from "../tipos/movimiento"
import { extremosDelActa, nombreDelActa } from "../tipos/revision"

const columnas = [
  "Acta",
  "Movimiento",
  "Destino",
  "Fecha del hecho",
  "Observó",
  "Motivo de la observación",
]

export const ObservadosPagina = () => {
  const { data: yo } = useQuery({ queryKey: ["yo"], queryFn: obtenerYo, retry: false })
  const direccion = yo?.unidad.nivel === "DIRECCION"
  const {
    data: observados,
    isPending,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["observados"],
    queryFn: obtenerObservados,
    enabled: !!yo && !direccion,
    retry: false,
  })
  const [abierto, setAbierto] = useState<Movimiento | null>(null)

  if (direccion) return <Navigate to="/" replace />

  return (
    <section className="flex flex-col gap-6">
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-2xl leading-tight font-semibold tracking-tight">Observados</h1>
      </div>
      {isPending ? (
        <div aria-busy="true" className="space-y-2">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-10 animate-pulse rounded-xs bg-gray-200" />
          ))}
        </div>
      ) : isError ? (
        <div role="alert" className="space-y-3 rounded-xs border border-error p-4 text-error">
          <p>{error.message}</p>
          <Boton variant="contorno" onClick={() => refetch()}>
            Reintentar
          </Boton>
        </div>
      ) : observados.length === 0 ? (
        <p className="p-4 text-gray-600">No hay movimientos observados</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-500">
              <tr>
                {columnas.map((columna) => (
                  <th
                    key={columna}
                    scope="col"
                    className="px-3 py-2 font-semibold whitespace-nowrap"
                  >
                    {columna}
                  </th>
                ))}
                <th scope="col" className="px-3 py-2">
                  <span className="sr-only">Acciones</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {observados.map((acta) => {
                const observacion = ultimaObservacion(acta)
                return (
                  <tr key={acta.id} className="border-b border-gray-200 align-top">
                    <td className="px-3 py-2 font-mono">{acta.numero_acta}</td>
                    <td className="px-3 py-2">
                      <span className="inline-flex items-center gap-2">
                        {nombreDelActa(acta)}
                        {acta.version_vigente > 0 && <Marca tono="secundario">Corregida</Marca>}
                      </span>
                    </td>
                    <td className="px-3 py-2">{extremosDelActa(acta).destino}</td>
                    <td className="px-3 py-2 font-mono">{fechaLegible(acta.fecha_hecho)}</td>
                    <td className="px-3 py-2 font-mono">{observacion?.usuario}</td>
                    <td className="max-w-md px-3 py-2">
                      <p className="line-clamp-2">{observacion?.motivo_observacion}</p>
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Boton
                        variant="contorno"
                        onClick={() => setAbierto(acta)}
                        className="px-3 py-1.5 text-sm"
                      >
                        Corregir
                      </Boton>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
      {abierto && (
        <ModalRectificacion key={abierto.id} acta={abierto} onCerrar={() => setAbierto(null)} />
      )}
    </section>
  )
}
