import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { obtenerPorRecibir } from "../api/movimientos"
import { Boton } from "../componentes/Boton"
import { ModalRecepcion } from "../componentes/ModalRecepcion"
import { areaDelTipo } from "../tipos/bien"
import {
  cambiarControl,
  fechaLegible,
  type ControlActa,
  type ControlBien,
  type Movimiento,
} from "../tipos/movimiento"

const columnas = ["Acta", "Origen", "Fecha del hecho", "Bienes"]

const sinControl: ControlActa = {}

export const PorRecibirPagina = () => {
  const {
    data: actas,
    isPending,
    isError,
    error,
    refetch,
  } = useQuery({ queryKey: ["por-recibir"], queryFn: obtenerPorRecibir, retry: false })
  const [abierta, setAbierta] = useState<Movimiento | null>(null)
  const [controles, setControles] = useState<Record<number, ControlActa>>({})

  const handleCambiar = (bienId: number, cambio: Partial<ControlBien>) => {
    if (!abierta) return
    const actaId = abierta.id
    setControles((actual) => ({
      ...actual,
      [actaId]: { ...actual[actaId], [bienId]: cambiarControl(actual[actaId]?.[bienId], cambio) },
    }))
  }

  const handleCerrar = () => setAbierta(null)

  const handleTerminada = () => {
    if (!abierta) return
    const actaId = abierta.id
    setControles((actual) => {
      const resto = { ...actual }
      delete resto[actaId]
      return resto
    })
    setAbierta(null)
  }

  return (
    <section className="flex flex-col gap-6">
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-2xl leading-tight font-semibold tracking-tight">Por recibir</h1>
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
      ) : actas.length === 0 ? (
        <p className="p-4 text-gray-600">No hay entregas para recibir</p>
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
              {actas.map((acta) => (
                <tr key={acta.id} className="border-b border-gray-200">
                  <td className="px-3 py-2 font-mono">{acta.numero_acta}</td>
                  <td className="px-3 py-2">{acta.unidad_origen?.nombre}</td>
                  <td className="px-3 py-2 font-mono">{fechaLegible(acta.fecha_hecho)}</td>
                  <td className="px-3 py-2">
                    {acta.bienes.length} · {areaDelTipo[acta.bienes[0]?.tipo_bien]}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <Boton
                      variant="contorno"
                      onClick={() => setAbierta(acta)}
                      className="px-3 py-1.5 text-sm"
                    >
                      Recibir
                    </Boton>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {abierta && (
        <ModalRecepcion
          key={abierta.id}
          acta={abierta}
          control={controles[abierta.id] ?? sinControl}
          onCambiar={handleCambiar}
          onCerrar={handleCerrar}
          onTerminada={handleTerminada}
        />
      )}
    </section>
  )
}
