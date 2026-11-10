import type { ReactNode } from "react"
import { areasDe, oficialesDe, type FilaInventario } from "../tipos/bien"
import { Boton } from "./Boton"

export type AvisoBarra = "areas" | "oficiales" | "fueraDeServicio" | "mismoTipo"

const textoAviso: Record<AvisoBarra, string> = {
  areas:
    "Un acta incluye bienes de una sola área: armamento y chalecos, o móviles y equipos de comunicaciones.",
  oficiales: "Una devolución es de un solo oficial. Dejá tildados solo los bienes de uno.",
  fueraDeServicio: "Un bien fuera de servicio no se asigna en dotación. Destildalo para seguir.",
  mismoTipo: "Un oficial recibe un solo bien de cada tipo. Dejá tildado uno de cada tipo.",
}

type BarraSeleccionProps = {
  seleccion: FilaInventario[]
  aviso: AvisoBarra | null
  onLimpiar: () => void
  onNuevaEntrega: () => void
  onAsignarAOficial: () => void
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
  aviso,
  onLimpiar,
  onNuevaEntrega,
  onAsignarAOficial,
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
      {aviso && <Aviso>{textoAviso[aviso]}</Aviso>}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xs bg-marca px-4 py-3 text-sm text-gray-50 shadow-lg">
        <span>
          <span className="font-semibold">
            {seleccion.length === 1
              ? "1 bien seleccionado"
              : `${seleccion.length} bienes seleccionados`}
          </span>
          <span className={areas.length > 1 ? "text-pendiente" : "text-gray-300"}>
            {" · "}
            {areas.length > 1 ? "Dos áreas" : areas[0]}
          </span>
          {devolucion && (
            <span className={oficiales.length > 1 ? "text-pendiente" : "text-gray-300"}>
              {" · "}
              {oficiales.length > 1 ? "Dos oficiales" : seleccion[0].oficial}
            </span>
          )}
        </span>
        <div className="flex flex-wrap gap-2">
          <Boton variant="contorno" onClick={onLimpiar} className="px-3 py-1.5">
            Limpiar
          </Boton>
          {devolucion && (
            <Boton variant="claro" onClick={onRegistrarDevolucion} className="px-3 py-1.5">
              Registrar devolución
            </Boton>
          )}
          {enDotacion === 0 && (
            <>
              <Boton variant="claro" onClick={onNuevaEntrega} className="px-3 py-1.5">
                Nueva entrega
              </Boton>
              <Boton variant="claro" onClick={onAsignarAOficial} className="px-3 py-1.5">
                Asignar a oficial
              </Boton>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
