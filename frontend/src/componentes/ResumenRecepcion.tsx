import { tiposDeBien } from "../tipos/bien"
import { fechaLegible, type Movimiento } from "../tipos/movimiento"

export const ResumenRecepcion = ({ movimiento }: { movimiento: Movimiento }) => {
  const aceptada = movimiento.estado === "APLICADO"
  return (
    <div className="flex flex-col gap-4">
      <p
        role="status"
        className="rounded-xs border border-exito bg-exito/5 px-4 py-3 text-sm font-semibold text-green-900"
      >
        {aceptada
          ? "Los bienes ya están en el inventario de la unidad."
          : "Los bienes siguen en la unidad de origen."}
      </p>
      <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
        <dt className="font-semibold">Acta</dt>
        <dd className="font-mono">{movimiento.numero_acta}</dd>
        <dt className="font-semibold">Origen</dt>
        <dd>{movimiento.unidad_origen?.nombre}</dd>
        <dt className="font-semibold">Fecha del hecho</dt>
        <dd className="font-mono">{fechaLegible(movimiento.fecha_hecho)}</dd>
      </dl>
      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold">Bienes · {movimiento.bienes.length}</h3>
        <ul className="divide-y divide-gray-100 rounded-xs border border-gray-200">
          {movimiento.bienes.map((bien) => (
            <li key={bien.bien_id} className="flex justify-between gap-3 px-3 py-2 text-sm">
              <span>
                {tiposDeBien[bien.tipo_bien] ?? bien.tipo_bien} ·{" "}
                <span className="font-mono">{bien.identificacion}</span> · {bien.marca}{" "}
                {bien.modelo}
              </span>
              {aceptada && <span className="shrink-0 text-gray-600">{bien.ubicacion_destino}</span>}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
