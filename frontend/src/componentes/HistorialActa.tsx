import { fechaHoraLegible, type Movimiento } from "../tipos/movimiento"
import { historialActa } from "../tipos/revision"

export const HistorialActa = ({ acta }: { acta: Movimiento }) => {
  const eventos = historialActa(acta)
  if (eventos.length === 0) return null
  return (
    <ul className="flex flex-col gap-1.5 rounded-xs border border-secundario bg-slate-50 px-4 py-3 text-sm text-gray-700">
      {eventos.map((evento, i) => (
        <li key={i}>
          <span className="font-semibold text-gray-900">{evento.accion}</span> por{" "}
          <span className="font-mono">{evento.usuario}</span> el{" "}
          <span className="font-mono">{fechaHoraLegible(evento.fecha)}</span>
          {evento.motivo && `: ${evento.motivo}`}
        </li>
      ))}
    </ul>
  )
}
