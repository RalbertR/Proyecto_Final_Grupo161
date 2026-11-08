import type { ReactNode } from "react"
import { areasDe, oficialesDe, type FilaInventario } from "../tipos/bien"
import { Boton } from "./Boton"

type BarraSeleccionProps = {
  seleccion: FilaInventario[]
  avisoArea: boolean
  avisoOficial: boolean
  onLimpiar: () => void
  onNuevaEntrega: () => void
  onRegistrarDevolucion: () => void
}

const Aviso = ({ children }: { children: ReactNode }) => (
  <div
    role="alert"
    className="rounded-xs border border-error bg-white px-4 py-3 text-sm font-medium text-error"
  >
    {children}
  </div>
)

export const BarraSeleccion = ({
  seleccion,
  avisoArea,
  avisoOficial,
  onLimpiar,
  onNuevaEntrega,
  onRegistrarDevolucion,
}: BarraSeleccionProps) => {
  if (seleccion.length === 0) return null
  const areas = areasDe(seleccion)
  const oficiales = oficialesDe(seleccion)
  const enDotacion = seleccion.filter((b) => b.tenencia === "DOTACION").length
  const mezclado = enDotacion > 0 && enDotacion < seleccion.length
  const devolucion = enDotacion === seleccion.length

  return (
    <div className="sticky bottom-4 flex flex-col gap-2">
      {mezclado && (
        <Aviso>
          Una entrega es de bienes en depósito y una devolución de bienes asignados a un oficial.
        </Aviso>
      )}
      {avisoOficial && (
        <Aviso>Una devolución es de un solo oficial. Dejá tildados solo los bienes de uno.</Aviso>
      )}
      {avisoArea && (
        <Aviso>
          Un acta incluye bienes de una sola área: armamento y chalecos, o móviles y equipos de
          comunicaciones.
        </Aviso>
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
          {devolucion && (
            <span className={oficiales.length > 1 ? "text-amber-300" : "text-gray-300"}>
              {" · "}
              {oficiales.length > 1 ? "Dos oficiales" : seleccion[0].oficial}
            </span>
          )}
        </span>
        <div className="flex gap-2">
          <Boton variant="contorno" onClick={onLimpiar} className="px-3 py-1.5">
            Limpiar
          </Boton>
          {!mezclado && (
            <Boton
              variant="claro"
              onClick={devolucion ? onRegistrarDevolucion : onNuevaEntrega}
              className="px-3 py-1.5"
            >
              {devolucion ? "Registrar devolución" : "Nueva entrega"}
            </Boton>
          )}
        </div>
      </div>
    </div>
  )
}
