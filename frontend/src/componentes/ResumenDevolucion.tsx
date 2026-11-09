import { tiposDeBien } from "../tipos/bien"
import { fechaLegible, textoRevision, type Movimiento } from "../tipos/movimiento"
import { textoOficial } from "../tipos/revision"
import { DocumentosActa } from "./DocumentosActa"
import { Marca } from "./Marca"

export const ResumenDevolucion = ({ movimiento }: { movimiento: Movimiento }) => (
  <div className="flex flex-col gap-4">
    <p
      role="status"
      className="rounded-xs border border-exito bg-exito/5 px-4 py-3 text-sm font-semibold text-green-900"
    >
      Los bienes volvieron al depósito.
    </p>
    <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
      <dt className="font-semibold">Acta</dt>
      <dd className="font-mono">{movimiento.numero_acta}</dd>
      <dt className="font-semibold">Estado</dt>
      <dd>
        <Marca tono="secundario">Aplicada</Marca>
      </dd>
      <dt className="font-semibold">Oficial</dt>
      <dd>{movimiento.oficial_origen && textoOficial(movimiento.oficial_origen)}</dd>
      <dt className="font-semibold">Fecha del hecho</dt>
      <dd className="font-mono">{fechaLegible(movimiento.fecha_hecho)}</dd>
      <dt className="font-semibold">Revisión</dt>
      <dd>{textoRevision[movimiento.estado_revision] ?? movimiento.estado_revision}</dd>
    </dl>
    <DocumentosActa movimientoId={movimiento.id} />
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-semibold">Bienes · {movimiento.bienes.length}</h3>
      <ul className="divide-y divide-gray-100 rounded-xs border border-gray-200">
        {movimiento.bienes.map((bien) => (
          <li key={bien.bien_id} className="px-3 py-2 text-sm">
            {tiposDeBien[bien.tipo_bien] ?? bien.tipo_bien} ·{" "}
            <span className="font-mono">{bien.identificacion}</span> · {bien.marca} {bien.modelo}
            <span className="text-gray-500"> · Queda en {bien.ubicacion_destino}</span>
          </li>
        ))}
      </ul>
    </div>
  </div>
)
