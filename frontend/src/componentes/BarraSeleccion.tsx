import { areasDe, type FilaInventario } from "../tipos/bien"
import { Boton } from "./Boton"

type BarraSeleccionProps = {
  seleccion: FilaInventario[]
  avisoArea: boolean
  onLimpiar: () => void
  onNuevaEntrega: () => void
}

export const BarraSeleccion = ({
  seleccion,
  avisoArea,
  onLimpiar,
  onNuevaEntrega,
}: BarraSeleccionProps) => {
  if (seleccion.length === 0) return null
  const areas = areasDe(seleccion)

  return (
    <div className="sticky bottom-4 flex flex-col gap-2">
      {avisoArea && (
        <div
          role="alert"
          className="rounded-xs border border-error bg-white px-4 py-3 text-sm font-medium text-error"
        >
          Un acta incluye bienes de una sola área: armamento y chalecos, o móviles y equipos de
          comunicaciones.
        </div>
      )}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xs bg-marca px-4 py-3 text-sm text-gray-50 shadow-lg">
        <span>
          <span className="font-semibold">
            {seleccion.length === 1
              ? "1 bien seleccionado"
              : `${seleccion.length} bienes seleccionados`}
          </span>
          <span className={areas.length > 1 ? "text-amber-300" : "text-gray-300"}>
            {" · "}
            {areas.length > 1 ? "Dos áreas" : areas[0]}
          </span>
        </span>
        <div className="flex gap-2">
          <Boton variant="contorno" onClick={onLimpiar} className="px-3 py-1.5">
            Limpiar
          </Boton>
          <Boton variant="claro" onClick={onNuevaEntrega} className="px-3 py-1.5">
            Nueva entrega
          </Boton>
        </div>
      </div>
    </div>
  )
}
