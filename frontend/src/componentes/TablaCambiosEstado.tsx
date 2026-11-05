import { nombreEstadoOperativo } from "../tipos/bien"
import { marcaEvento, type EventoHistorial } from "../tipos/historial"
import { fechaLegible } from "../tipos/movimiento"
import { Marca } from "./Marca"

const columnas = ["Fecha", "Pasó a", "Motivo", "Revisión"]

export const TablaCambiosEstado = ({ eventos }: { eventos: EventoHistorial[] }) => {
  if (eventos.length === 0)
    return <p className="py-2 text-gray-600">Este bien no tiene cambios de estado registrados</p>
  return (
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
                <td className="px-3 py-2 align-top">
                  <Marca tono={marca.tono}>{marca.texto}</Marca>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
