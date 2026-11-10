import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { fresca, porId, useAbrirDesdeInicio } from "../estado/abrirDesdeInicio"
import { Navigate } from "react-router-dom"
import { obtenerYo } from "../api/auth"
import { obtenerCambiosObservados } from "../api/cambiosEstado"
import { obtenerObservados } from "../api/movimientos"
import { Boton } from "../componentes/Boton"
import { Marca } from "../componentes/Marca"
import { ModalCorreccionCambio } from "../componentes/ModalCorreccionCambio"
import { ModalRectificacion } from "../componentes/ModalRectificacion"
import { nombreEstadoOperativo } from "../tipos/bien"
import { ultimaObservacionCambio, type CambioEstado } from "../tipos/cambioEstado"
import {
  fechaHoraLegible,
  fechaLegible,
  ultimaObservacion,
  type Movimiento,
} from "../tipos/movimiento"
import { extremosDelActa, nombreDelActa } from "../tipos/revision"

const columnas = [
  "Acta",
  "Movimiento",
  "Destino",
  "Fecha del hecho",
  "Observó",
  "Motivo de la observación",
]

const columnasCambios = ["Bien", "Pasó a", "Fecha", "Observó", "Motivo de la observación"]

const Encabezado = ({ titulos }: { titulos: string[] }) => (
  <thead className="border-b border-gray-500">
    <tr>
      {titulos.map((titulo) => (
        <th key={titulo} scope="col" className="px-3 py-2 font-semibold whitespace-nowrap">
          {titulo}
        </th>
      ))}
      <th scope="col" className="px-3 py-2">
        <span className="sr-only">Acciones</span>
      </th>
    </tr>
  </thead>
)

export const ObservadosPagina = () => {
  const { data: yo } = useQuery({ queryKey: ["yo"], queryFn: obtenerYo, retry: false })
  const direccion = yo?.unidad.nivel === "DIRECCION"
  const actas = useQuery({
    queryKey: ["observados"],
    queryFn: obtenerObservados,
    enabled: !!yo && !direccion,
    retry: false,
  })
  const cambios = useQuery({
    queryKey: ["cambios-observados"],
    queryFn: obtenerCambiosObservados,
    enabled: !!yo && !direccion,
    retry: false,
  })
  const [abierto, setAbierto] = useState<Movimiento | null>(null)
  const [cambioAbierto, setCambioAbierto] = useState<CambioEstado | null>(null)
  useAbrirDesdeInicio(
    fresca(actas.data, actas.isFetchedAfterMount, actas.isFetching),
    "MOVIMIENTO",
    porId,
    setAbierto,
  )
  useAbrirDesdeInicio(
    fresca(cambios.data, cambios.isFetchedAfterMount, cambios.isFetching),
    "CAMBIO_ESTADO",
    porId,
    setCambioAbierto,
  )

  if (direccion) return <Navigate to="/" replace />

  const contenido = () => {
    if (actas.isPending || cambios.isPending)
      return (
        <div aria-busy="true" className="space-y-2">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-10 animate-pulse rounded-xs bg-gray-200" />
          ))}
        </div>
      )
    if (actas.isError || cambios.isError)
      return (
        <div role="alert" className="space-y-3 rounded-xs border border-error p-4 text-error">
          <p>{(actas.error ?? cambios.error)?.message}</p>
          <Boton
            variant="contorno"
            onClick={() => {
              actas.refetch()
              cambios.refetch()
            }}
          >
            Reintentar
          </Boton>
        </div>
      )
    if (actas.data.length === 0 && cambios.data.length === 0)
      return <p className="p-4 text-gray-600">No hay registros observados</p>
    return (
      <>
        {actas.data.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full bg-white text-left text-sm">
              <Encabezado titulos={columnas} />
              <tbody>
                {actas.data.map((acta) => {
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
        {cambios.data.length > 0 && (
          <section aria-labelledby="titulo-cambios" className="flex flex-col gap-2">
            <h2 id="titulo-cambios" className="text-lg font-semibold">
              Cambios de estado
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full bg-white text-left text-sm">
                <Encabezado titulos={columnasCambios} />
                <tbody>
                  {cambios.data.map((cambio) => {
                    const observacion = ultimaObservacionCambio(cambio)
                    return (
                      <tr key={cambio.id} className="border-b border-gray-200 align-top">
                        <td className="px-3 py-2">
                          <span className="inline-flex items-center gap-2">
                            <span className="font-mono">{cambio.bien.identificacion}</span>
                            {cambio.version_vigente > 0 && (
                              <Marca tono="secundario">Corregido</Marca>
                            )}
                          </span>
                        </td>
                        <td className="px-3 py-2">{nombreEstadoOperativo[cambio.estado_nuevo]}</td>
                        <td className="px-3 py-2 font-mono">{fechaHoraLegible(cambio.fecha)}</td>
                        <td className="px-3 py-2 font-mono">{observacion?.usuario}</td>
                        <td className="max-w-md px-3 py-2">
                          <p className="line-clamp-2">{observacion?.motivo_observacion}</p>
                        </td>
                        <td className="px-3 py-2 text-right">
                          <Boton
                            variant="contorno"
                            onClick={() => setCambioAbierto(cambio)}
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
          </section>
        )}
      </>
    )
  }

  return (
    <section className="flex flex-col gap-6">
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-2xl leading-tight font-semibold tracking-tight">Observados</h1>
      </div>
      {contenido()}
      {abierto && (
        <ModalRectificacion key={abierto.id} acta={abierto} onCerrar={() => setAbierto(null)} />
      )}
      {cambioAbierto && (
        <ModalCorreccionCambio
          key={cambioAbierto.id}
          cambio={cambioAbierto}
          onCerrar={() => setCambioAbierto(null)}
        />
      )}
    </section>
  )
}
