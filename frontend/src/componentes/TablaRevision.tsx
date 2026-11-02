import { tiposDeBien } from "../tipos/bien"
import type { Movimiento } from "../tipos/movimiento"
import type { ControlRevision } from "../tipos/revision"

const columnas = [
  "Coincide",
  "Tipo",
  "Marca",
  "Modelo",
  "Número de serie / Dominio",
  "Ubicación en destino",
]

type TablaRevisionProps = {
  acta: Movimiento
  control: ControlRevision
  onCambiar: (control: ControlRevision) => void
}

export const TablaRevision = ({ acta, control, onCambiar }: TablaRevisionProps) => (
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
        {acta.bienes.map((bien) => (
          <tr key={bien.bien_id} className="border-b border-gray-200">
            <td className="px-3 py-1">
              <label className="inline-flex size-6 items-center">
                <input
                  type="checkbox"
                  checked={!!control.bienes[bien.bien_id]}
                  onChange={(e) =>
                    onCambiar({
                      ...control,
                      bienes: { ...control.bienes, [bien.bien_id]: e.target.checked },
                    })
                  }
                  aria-label={`Coincide ${bien.identificacion}`}
                  className="size-4 accent-marca focus-visible:outline-3 focus-visible:outline-foco"
                />
              </label>
            </td>
            <td className="px-3 py-2">{tiposDeBien[bien.tipo_bien] ?? bien.tipo_bien}</td>
            <td className="px-3 py-2">{bien.marca}</td>
            <td className="px-3 py-2">{bien.modelo}</td>
            <td className="px-3 py-2 font-mono">{bien.identificacion}</td>
            <td className="px-3 py-2">{bien.ubicacion_destino}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
)
