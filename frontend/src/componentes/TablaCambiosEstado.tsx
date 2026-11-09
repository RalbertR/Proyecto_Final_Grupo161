import { useMutation } from "@tanstack/react-query"
import { obtenerInforme } from "../api/cambiosEstado"
import { nombreEstadoOperativo } from "../tipos/bien"
import { marcaEvento, type BienHistorial, type EventoHistorial } from "../tipos/historial"
import { fechaLegible } from "../tipos/movimiento"
import { descargarPdf } from "../tipos/documento"
import { Marca } from "./Marca"

const columnas = ["Fecha", "Pasó a", "Motivo", "Informe", "Revisión"]

type TablaCambiosEstadoProps = {
  bien: BienHistorial
  eventos: EventoHistorial[]
}

export const TablaCambiosEstado = ({ bien, eventos }: TablaCambiosEstadoProps) => {
  const descarga = useMutation({
    mutationFn: async (evento: EventoHistorial) =>
      descargarPdf(
        await obtenerInforme(evento.registro_id),
        `informe ${bien.identificacion} ${evento.fecha}.pdf`,
      ),
  })

  if (eventos.length === 0)
    return <p className="py-2 text-gray-600">Este bien no tiene cambios de estado registrados</p>
  return (
    <div className="flex flex-col gap-2">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-500">
            <tr>
              {columnas.map((columna) => (
                <th key={columna} scope="col" className="px-3 py-2 font-semibold whitespace-nowrap">
                  {columna}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {eventos.map((evento) => {
              const marca = marcaEvento(evento)
              return (
                <tr key={evento.registro_id} className="border-b border-gray-200">
                  <td className="px-3 py-2 align-top font-mono whitespace-nowrap">
                    {fechaLegible(evento.fecha)}
                  </td>
                  <td className="px-3 py-2 align-top whitespace-nowrap">
                    {evento.estado_operativo_nuevo &&
                      nombreEstadoOperativo[evento.estado_operativo_nuevo]}
                  </td>
                  <td className="px-3 py-2 align-top">{evento.detalle}</td>
                  <td className="px-3 py-2 align-top whitespace-nowrap">
                    {evento.tiene_informe ? (
                      <button
                        type="button"
                        disabled={descarga.isPending}
                        onClick={() => descarga.mutate(evento)}
                        className="font-semibold text-marca underline hover:text-marca-hover focus-visible:outline-3 focus-visible:outline-foco disabled:opacity-50"
                      >
                        {descarga.isPending && descarga.variables.registro_id === evento.registro_id
                          ? "Descargando…"
                          : "Descargar"}
                      </button>
                    ) : (
                      <span className="text-gray-500">Sin informe</span>
                    )}
                  </td>
                  <td className="px-3 py-2 align-top">
                    <Marca tono={marca.tono}>{marca.texto}</Marca>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      {descarga.error && (
        <p
          role="alert"
          className="rounded-xs border border-error bg-error/5 px-4 py-3 text-sm text-error"
        >
          {descarga.error.message}
        </p>
      )}
    </div>
  )
}
