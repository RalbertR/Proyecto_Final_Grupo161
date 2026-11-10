import { marcaEvento, type EventoHistorial } from "../tipos/historial"
import { fechaLegible } from "../tipos/movimiento"
import { nombreMovimiento } from "../tipos/revision"
import { Marca } from "./Marca"

const columnas = ["Fecha", "Movimiento", "Acta", "Origen", "Destino", "Unidad dueña", "Estado"]

type TablaMovimientosBienProps = {
  eventos: EventoHistorial[]
  onAbrirActa: (movimientoId: number) => void
}

export const TablaMovimientosBien = ({ eventos, onAbrirActa }: TablaMovimientosBienProps) => {
  if (eventos.length === 0)
    return <p className="py-2 text-gray-600">Este bien no tiene movimientos registrados</p>
  return (
    <div className="overflow-x-auto">
      <table className="w-full bg-white text-left text-sm">
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
                <td className="px-3 py-2 align-top">
                  {nombreMovimiento(
                    evento.evento,
                    evento.oficial_origen_id !== null,
                    evento.oficial_destino_id !== null,
                  )}
                </td>
                <td className="px-3 py-2 align-top whitespace-nowrap">
                  {evento.numero_acta ? (
                    <button
                      type="button"
                      onClick={() => onAbrirActa(evento.registro_id)}
                      className="font-mono font-semibold text-marca underline hover:text-marca-hover focus-visible:outline-3 focus-visible:outline-foco"
                    >
                      {evento.numero_acta}
                    </button>
                  ) : (
                    "Sin acta"
                  )}
                </td>
                <td className="px-3 py-2 align-top">{evento.origen ?? "No aplica"}</td>
                <td className="px-3 py-2 align-top">{evento.destino ?? "No aplica"}</td>
                <td className="px-3 py-2 align-top">{evento.unidad_duena}</td>
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
