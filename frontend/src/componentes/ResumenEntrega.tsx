import { tiposDeBien } from "../tipos/bien"
import { fechaLegible, type Movimiento } from "../tipos/movimiento"
import { Marca } from "./Marca"

const textoRevision: Record<string, string> = {
  PENDIENTE: "Pendiente de la unidad superior",
  NO_APLICA: "No corresponde",
}

export const ResumenEntrega = ({ movimiento }: { movimiento: Movimiento }) => (
  <div className="flex flex-col gap-4">
    <p
      role="status"
      className="rounded-xs border border-exito bg-exito/5 px-4 py-3 text-sm font-semibold text-green-900"
    >
      El acta quedó pendiente de recepción.
    </p>
    <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
      <dt className="font-semibold">Acta</dt>
      <dd className="font-mono">{movimiento.numero_acta}</dd>
      <dt className="font-semibold">Estado</dt>
      <dd>
        <Marca>Pendiente</Marca>
      </dd>
      <dt className="font-semibold">Destino</dt>
      <dd>{movimiento.unidad_destino?.nombre}</dd>
      <dt className="font-semibold">Fecha del hecho</dt>
      <dd className="font-mono">{fechaLegible(movimiento.fecha_hecho)}</dd>
      <dt className="font-semibold">Revisión</dt>
      <dd>{textoRevision[movimiento.estado_revision] ?? movimiento.estado_revision}</dd>
    </dl>
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-semibold">Bienes · {movimiento.bienes.length}</h3>
      <ul className="divide-y divide-gray-100 rounded-xs border border-gray-200">
        {movimiento.bienes.map((bien) => (
          <li key={bien.bien_id} className="px-3 py-2 text-sm">
            {tiposDeBien[bien.tipo_bien] ?? bien.tipo_bien} ·{" "}
            <span className="font-mono">{bien.identificacion}</span> · {bien.marca} {bien.modelo}
          </li>
        ))}
      </ul>
    </div>
  </div>
)
