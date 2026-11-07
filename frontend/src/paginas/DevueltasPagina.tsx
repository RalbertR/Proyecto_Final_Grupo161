import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { obtenerDevueltas } from "../api/movimientos"
import { Boton } from "../componentes/Boton"
import { ModalCorreccion } from "../componentes/ModalCorreccion"
import { devoluciones, fechaHoraLegible, fechaLegible, type Movimiento } from "../tipos/movimiento"

const columnas = ["Acta", "Destino", "Fecha del hecho", "Devolvió", "Motivo", "Con novedad"]

export const DevueltasPagina = () => {
  const {
    data: devueltas,
    isPending,
    isError,
    error,
    refetch,
  } = useQuery({ queryKey: ["devueltas"], queryFn: obtenerDevueltas, retry: false })
  const [abierta, setAbierta] = useState<Movimiento | null>(null)

  return (
    <section className="flex flex-col gap-6">
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-2xl leading-tight font-semibold tracking-tight">Devueltas</h1>
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
      ) : devueltas.length === 0 ? (
        <p className="p-4 text-gray-600">No hay actas devueltas</p>
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
              {devueltas.map((acta) => {
                const ultima = devoluciones(acta)[0]
                return (
                  <tr key={acta.id} className="border-b border-gray-200 align-top">
                    <td className="px-3 py-2 font-mono">{acta.numero_acta}</td>
                    <td className="px-3 py-2">{acta.unidad_destino?.nombre}</td>
                    <td className="px-3 py-2 font-mono">{fechaLegible(acta.fecha_hecho)}</td>
                    <td className="px-3 py-2">
                      {ultima && (
                        <span className="flex flex-col font-mono">
                          <span>{ultima.usuario}</span>
                          <span className="text-gray-500">{fechaHoraLegible(ultima.fecha)}</span>
                        </span>
                      )}
                    </td>
                    <td className="max-w-md px-3 py-2">
                      <p className="line-clamp-2">{ultima?.motivo}</p>
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap">
                      {ultima?.bienes_con_novedad.length ?? 0} de {acta.bienes.length}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Boton
                        variant="contorno"
                        onClick={() => setAbierta(acta)}
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
      {abierta && (
        <ModalCorreccion
          key={abierta.id}
          acta={abierta}
          onCerrar={() => setAbierta(null)}
          onTerminada={() => setAbierta(null)}
        />
      )}
    </section>
  )
}
