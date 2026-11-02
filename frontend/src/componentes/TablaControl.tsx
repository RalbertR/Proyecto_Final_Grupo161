import { tiposDeBien } from "../tipos/bien"
import {
  ubicacionPorDefecto,
  type ControlActa,
  type ControlBien,
  type RenglonMovimiento,
} from "../tipos/movimiento"
import type { Ubicacion } from "../tipos/unidad"

const columnas = [
  "Controlado",
  "Con novedad",
  "Tipo",
  "Marca",
  "Modelo",
  "Número de serie / Dominio",
  "Estado",
  "Ubicación",
]

const claseCasilla = "size-4 focus-visible:outline-3 focus-visible:outline-foco"

type TablaControlProps = {
  bienes: RenglonMovimiento[]
  control: ControlActa
  ubicaciones: Ubicacion[]
  onCambiar: (bienId: number, cambio: Partial<ControlBien>) => void
}

export const TablaControl = ({ bienes, control, ubicaciones, onCambiar }: TablaControlProps) => (
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
        {bienes.map((bien) => {
          const estado = control[bien.bien_id]
          const ubicacionId =
            estado?.ubicacionId ?? ubicacionPorDefecto(bien.tipo_bien, ubicaciones)
          return (
            <tr
              key={bien.bien_id}
              className={`border-b border-gray-200 ${estado?.conNovedad ? "bg-pendiente/10" : ""}`}
            >
              <td className="px-3 py-1">
                <label className="inline-flex size-6 items-center">
                  <input
                    type="checkbox"
                    checked={!!estado?.controlado}
                    onChange={(e) => onCambiar(bien.bien_id, { controlado: e.target.checked })}
                    aria-label={`Controlado ${bien.identificacion}`}
                    className={`${claseCasilla} accent-marca`}
                  />
                </label>
              </td>
              <td className="px-3 py-1">
                <label className="inline-flex size-6 items-center">
                  <input
                    type="checkbox"
                    checked={!!estado?.conNovedad}
                    onChange={(e) => onCambiar(bien.bien_id, { conNovedad: e.target.checked })}
                    aria-label={`Con novedad ${bien.identificacion}`}
                    className={`${claseCasilla} accent-pendiente`}
                  />
                </label>
              </td>
              <td className="px-3 py-1">{tiposDeBien[bien.tipo_bien] ?? bien.tipo_bien}</td>
              <td className="px-3 py-1">{bien.marca}</td>
              <td className="px-3 py-1">{bien.modelo}</td>
              <td className="px-3 py-1 font-mono">{bien.identificacion}</td>
              <td className="px-3 py-1 whitespace-nowrap">
                {bien.estado_operativo === "EN_SERVICIO" ? "En servicio" : "Fuera de servicio"}
              </td>
              <td className="px-3 py-1">
                <select
                  value={ubicacionId ?? ""}
                  onChange={(e) =>
                    onCambiar(bien.bien_id, { ubicacionId: Number(e.target.value) || undefined })
                  }
                  aria-label={`Ubicación ${bien.identificacion}`}
                  className="min-h-11 rounded-xs border border-gray-300 bg-white px-3 py-2 hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco"
                >
                  <option value="">Elegí una ubicación</option>
                  {ubicaciones.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.nombre}
                    </option>
                  ))}
                </select>
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  </div>
)
