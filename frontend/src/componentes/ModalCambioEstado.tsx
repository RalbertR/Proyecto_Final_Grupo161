import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect, useId, useRef, useState, type FormEvent } from "react"
import { registrarCambio } from "../api/cambiosEstado"
import { ErrorHttp } from "../api/http"
import { nombreEstadoOperativo } from "../tipos/bien"
import { estadoOpuesto } from "../tipos/cambioEstado"
import type { BienHistorial } from "../tipos/historial"
import { Boton } from "./Boton"
import { CampoPdf } from "./CampoPdf"

const claseEstado =
  "rounded-xs border border-secundario bg-slate-50 px-3 py-1.5 text-sm font-semibold"

type ModalCambioEstadoProps = {
  bien: BienHistorial
  onCerrar: () => void
}

export const ModalCambioEstado = ({ bien, onCerrar }: ModalCambioEstadoProps) => {
  const tituloId = useId()
  const ayudaId = useId()
  const dialogo = useRef<HTMLDialogElement>(null)
  const enviando = useRef(false)
  const queryClient = useQueryClient()
  const [observaciones, setObservaciones] = useState("")
  const [informe, setInforme] = useState<File | null>(null)
  const [fallo, setFallo] = useState<{ mensaje: string; terminal: boolean } | null>(null)
  const estadoNuevo = estadoOpuesto(bien.estado_operativo)
  const fueraDeServicio = estadoNuevo === "FUERA_DE_SERVICIO"
  const { mutate, isPending } = useMutation({
    mutationFn: () => registrarCambio(bien.id, estadoNuevo, observaciones.trim(), informe),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["historial", bien.id] })
      queryClient.invalidateQueries({ queryKey: ["inventario"] })
      queryClient.invalidateQueries({ queryKey: ["bandeja"] })
      dialogo.current?.close()
    },
    onError: (e) => {
      const status = e instanceof ErrorHttp ? e.status : 0
      const terminal = status === 403 || status === 404
      if (status === 403 || status === 404 || status === 409)
        queryClient.invalidateQueries({ queryKey: ["historial", bien.id] })
      setFallo({ mensaje: e.message, terminal })
    },
    onSettled: () => {
      enviando.current = false
    },
  })

  useEffect(() => {
    const d = dialogo.current
    if (d && !d.open) d.showModal()
  }, [])

  useEffect(() => {
    const frenarEscape = (e: KeyboardEvent) => {
      if (enviando.current && e.key === "Escape") e.preventDefault()
    }
    document.addEventListener("keydown", frenarEscape, true)
    return () => document.removeEventListener("keydown", frenarEscape, true)
  }, [])

  const completo = !!observaciones.trim() && (!fueraDeServicio || !!informe)

  const handleEnviar = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (enviando.current || !completo) return
    enviando.current = true
    setFallo(null)
    mutate()
  }

  return (
    <dialog
      ref={dialogo}
      onCancel={(e) => {
        if (isPending) e.preventDefault()
      }}
      onClose={onCerrar}
      aria-labelledby={tituloId}
      className="m-auto w-full max-w-xl rounded-xs p-0 text-gray-900 shadow-xl backdrop:bg-gray-900/45"
    >
      <form onSubmit={handleEnviar} className="flex max-h-[90vh] flex-col">
        <header className="border-b border-gray-200 px-6 py-4">
          <h2 id={tituloId} className="text-lg font-semibold">
            Cambiar estado de <span className="font-mono">{bien.identificacion}</span>
          </h2>
          <p className="text-sm text-gray-600">
            {bien.marca} {bien.modelo}
          </p>
        </header>
        {fallo && (
          <div
            role="alert"
            className="mx-6 mt-4 rounded-xs border border-error bg-error/5 px-4 py-3 text-sm font-medium text-error"
          >
            {fallo.mensaje}
          </div>
        )}
        <div className="overflow-y-auto px-6 py-4">
          <fieldset
            disabled={isPending || !!fallo?.terminal}
            className="flex min-w-0 flex-col gap-4"
          >
            <div className="flex flex-col gap-2">
              <span className="text-sm font-semibold">Estado</span>
              <p className="flex flex-wrap items-center gap-2 text-sm">
                <span className={claseEstado}>{nombreEstadoOperativo[bien.estado_operativo]}</span>
                pasa a<span className={claseEstado}>{nombreEstadoOperativo[estadoNuevo]}</span>
              </p>
            </div>
            <label className="flex flex-col gap-2 text-sm font-semibold">
              Observaciones
              <textarea
                required
                maxLength={500}
                rows={3}
                aria-describedby={ayudaId}
                value={observaciones}
                onChange={(e) => setObservaciones(e.target.value)}
                className="min-h-11 rounded-xs border border-gray-300 bg-white px-3 py-2 font-normal hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco"
              />
              <span id={ayudaId} className="text-xs font-normal text-gray-500">
                {fueraDeServicio
                  ? "Obligatorio. Motivo por el que queda fuera de servicio."
                  : "Obligatorio. Qué se reparó y que quedó operativo."}
              </span>
            </label>
            <CampoPdf
              etiqueta={
                fueraDeServicio
                  ? "Informe técnico en PDF"
                  : "Informe de puesta en servicio en PDF, opcional"
              }
              ayuda={
                fueraDeServicio
                  ? "Obligatorio. El informe firmado y escaneado, de hasta 10 MB."
                  : "PDF de hasta 10 MB."
              }
              obligatorio={fueraDeServicio}
              deshabilitado={isPending}
              onElegir={setInforme}
            />
          </fieldset>
        </div>
        <footer className="flex justify-end gap-2 border-t border-gray-200 px-6 py-3">
          {fallo?.terminal ? (
            <Boton type="button" onClick={onCerrar}>
              Cerrar
            </Boton>
          ) : (
            <>
              <Boton type="button" variant="contorno" onClick={onCerrar} disabled={isPending}>
                Cancelar
              </Boton>
              <Boton type="submit" disabled={!completo || isPending}>
                {isPending ? "Registrando…" : "Registrar cambio"}
              </Boton>
            </>
          )}
        </footer>
      </form>
    </dialog>
  )
}
