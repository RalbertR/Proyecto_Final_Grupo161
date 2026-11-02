import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { Navigate } from "react-router-dom"
import { obtenerYo } from "../api/auth"
import { obtenerMovimientosARevisar } from "../api/revisiones"
import { Boton } from "../componentes/Boton"
import { Marca } from "../componentes/Marca"
import { ModalRevision } from "../componentes/ModalRevision"
import { fechaLegible } from "../tipos/movimiento"
import { nombreEvento, type ControlRevision } from "../tipos/revision"

const columnas = ["Acta", "Movimiento", "Origen", "Destino", "Fecha del hecho", "Cargó"]

export const RevisionPagina = () => {
  const { data: yo } = useQuery({ queryKey: ["yo"], queryFn: obtenerYo, retry: false })
  const operacional = yo?.unidad.nivel === "OPERACIONAL"
  const {
    data: registros,
    isPending,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["bandeja"],
    queryFn: obtenerMovimientosARevisar,
    enabled: !!yo && !operacional,
    retry: false,
  })
  const [abierto, setAbierto] = useState<number | null>(null)
  const [controles, setControles] = useState<Record<number, ControlRevision>>({})

  if (operacional) return <Navigate to="/" replace />

  const handleCambiar = (control: ControlRevision) => {
    if (abierto === null) return
    setControles((actual) => ({ ...actual, [abierto]: control }))
  }

  const handleCerrar = () => setAbierto(null)

  const handleTerminada = () => {
    if (abierto === null) return
    const id = abierto
    setControles((actual) => {
      const resto = { ...actual }
      delete resto[id]
      return resto
    })
    setAbierto(null)
  }

  return (
    <section className="flex flex-col gap-6">
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-2xl leading-tight font-semibold tracking-tight">Revisión</h1>
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
      ) : registros.length === 0 ? (
        <p className="p-4 text-gray-600">No hay registros para revisar</p>
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
              {registros.map((registro) => (
                <tr key={registro.registro_id} className="border-b border-gray-200">
                  <td className="px-3 py-2 font-mono">{registro.numero_acta}</td>
                  <td className="px-3 py-2">
                    <span className="inline-flex items-center gap-2">
                      {nombreEvento[registro.evento] ?? registro.evento}
                      {registro.version > 0 && <Marca tono="secundario">Corregida</Marca>}
                    </span>
                  </td>
                  <td className="px-3 py-2">{registro.unidad_origen}</td>
                  <td className="px-3 py-2">{registro.unidad_destino}</td>
                  <td className="px-3 py-2 font-mono">{fechaLegible(registro.fecha)}</td>
                  <td className="px-3 py-2 font-mono">{registro.usuario}</td>
                  <td className="px-3 py-2 text-right">
                    <Boton
                      variant="contorno"
                      onClick={() => setAbierto(registro.registro_id)}
                      className="px-3 py-1.5 text-sm"
                    >
                      Revisar
                    </Boton>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {abierto !== null && (
        <ModalRevision
          key={abierto}
          movimientoId={abierto}
          control={controles[abierto]}
          onCambiar={handleCambiar}
          onCerrar={handleCerrar}
          onTerminada={handleTerminada}
        />
      )}
    </section>
  )
}
