import { tiposDeBien } from "../tipos/bien"
import type { Movimiento } from "../tipos/movimiento"

const columnas = ["Tipo", "Marca", "Modelo", "Número de serie / Dominio"]

export const BienesActa = ({ acta }: { acta: Movimiento }) => (
  <details open className="text-sm">
    <summary className="cursor-pointer font-semibold">
      Bienes del acta ({acta.bienes.length})
    </summary>
    <div className="mt-2 overflow-x-auto">
      <table className="w-full text-left">
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
              <td className="px-3 py-2">{tiposDeBien[bien.tipo_bien] ?? bien.tipo_bien}</td>
              <td className="px-3 py-2">{bien.marca}</td>
              <td className="px-3 py-2">{bien.modelo}</td>
              <td className="px-3 py-2 font-mono">{bien.identificacion}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </details>
)
