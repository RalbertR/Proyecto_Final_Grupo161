import { useQuery } from "@tanstack/react-query"
import { useEffect, useRef } from "react"
import { obtenerMovimiento } from "../api/movimientos"
import { fechaLegible, type Movimiento } from "../tipos/movimiento"
import { historialActa, nombreEvento } from "../tipos/revision"
import { BienesActa } from "./BienesActa"
import { Boton } from "./Boton"
import { Dato } from "./Dato"
import { HistorialActa } from "./HistorialActa"
import { Marca } from "./Marca"

const DatosActa = ({ acta }: { acta: Movimiento }) => (
  <dl className="grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-3">
    <Dato etiqueta="Movimiento">{nombreEvento[acta.tipo] ?? acta.tipo}</Dato>
    <Dato etiqueta="Fecha del hecho">
      <span className="font-mono">{fechaLegible(acta.fecha_hecho)}</span>
    </Dato>
    <Dato etiqueta="Cargó">
      <span className="font-mono">{acta.usuario}</span>
    </Dato>
    <Dato etiqueta="Origen">{acta.unidad_origen?.nombre ?? "No aplica"}</Dato>
    <Dato etiqueta="Destino">{acta.unidad_destino?.nombre ?? "No aplica"}</Dato>
    {acta.descripcion && <Dato etiqueta="Descripción">{acta.descripcion}</Dato>}
  </dl>
)

type ModalActaProps = {
  movimientoId: number
  onCerrar: () => void
}

export const ModalActa = ({ movimientoId, onCerrar }: ModalActaProps) => {
  const dialogo = useRef<HTMLDialogElement>(null)
  const {
    data: acta,
    isError,
    error,
  } = useQuery({
    queryKey: ["movimiento", movimientoId],
    queryFn: () => obtenerMovimiento(movimientoId),
    retry: false,
    refetchOnWindowFocus: false,
    gcTime: 0,
  })

  useEffect(() => {
    const d = dialogo.current
    if (d && !d.open) d.showModal()
  }, [])

  return (
    <dialog
      ref={dialogo}
      onClose={onCerrar}
      aria-labelledby="titulo-acta"
      className="m-auto w-full max-w-4xl rounded-xs p-0 text-gray-900 shadow-xl backdrop:bg-gray-900/45"
    >
      <div className="flex max-h-[90vh] flex-col">
        <header className="border-b border-gray-200 px-6 py-4">
          <h2 id="titulo-acta" className="flex items-center gap-3 text-lg font-semibold">
            <span>
              Acta <span className="font-mono">{acta?.numero_acta}</span>
            </span>
            {!!acta?.version_vigente && <Marca tono="secundario">Corregida</Marca>}
          </h2>
        </header>
        <div className="flex flex-col gap-4 overflow-y-auto px-6 py-4">
          {isError && (
            <p
              role="alert"
              className="rounded-xs border border-error bg-error/5 px-4 py-3 text-sm font-medium text-error"
            >
              {error.message}
            </p>
          )}
          {!acta && !isError && (
            <div aria-busy="true" className="space-y-2">
              {[1, 2, 3].map((n) => (
                <div key={n} className="h-10 animate-pulse rounded-xs bg-gray-200" />
              ))}
            </div>
          )}
          {acta && (
            <>
              <DatosActa acta={acta} />
              <HistorialActa eventos={historialActa(acta)} />
              <BienesActa acta={acta} />
            </>
          )}
        </div>
        <footer className="flex justify-end border-t border-gray-200 px-6 py-3">
          <Boton type="button" variant="contorno" onClick={() => dialogo.current?.close()}>
            Cerrar
          </Boton>
        </footer>
      </div>
    </dialog>
  )
}
