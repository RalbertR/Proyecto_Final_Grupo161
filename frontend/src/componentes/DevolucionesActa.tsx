import { devoluciones, fechaHoraLegible, type Movimiento } from "../tipos/movimiento"

export const DevolucionesActa = ({ acta }: { acta: Movimiento }) => {
  const lista = devoluciones(acta)
  if (lista.length === 0) return null
  return (
    <section className="rounded-xs border border-gray-200 text-sm">
      <h3 className="border-b border-gray-200 bg-gray-50 px-4 py-2 font-semibold">
        {lista.length === 1 ? "Devuelta 1 vez" : `Devuelta ${lista.length} veces`}
      </h3>
      <ul className="divide-y divide-gray-100">
        {lista.map((devolucion, i) => (
          <li key={i} className="flex flex-col gap-1 px-4 py-2">
            <span>
              <span className="font-mono text-gray-600">{fechaHoraLegible(devolucion.fecha)}</span>
              {" · "}
              <span className="font-mono">{devolucion.usuario}</span>
              {devolucion.motivo && ` · ${devolucion.motivo}`}
            </span>
            {devolucion.bienes_con_novedad.length > 0 && (
              <span className="text-gray-600">
                Con novedad:{" "}
                <span className="font-mono">
                  {devolucion.bienes_con_novedad.map((n) => n.identificacion).join(", ")}
                </span>
              </span>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}
