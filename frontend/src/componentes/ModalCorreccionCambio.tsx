import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect, useId, useRef, useState, type FormEvent } from "react"
import { obtenerInforme, rectificarCambio } from "../api/cambiosEstado"
import { ErrorHttp } from "../api/http"
import { nombreEstadoOperativo } from "../tipos/bien"
import {
  historialCambio,
  ultimaObservacionCambio,
  type CambioEstado,
  type RectificacionCambioCreate,
} from "../tipos/cambioEstado"
import { descargarPdf } from "../tipos/documento"
import { fechaHoraLegible } from "../tipos/movimiento"
import { Boton } from "./Boton"
import { CampoPdf } from "./CampoPdf"
import { HistorialActa } from "./HistorialActa"

const claseError = "rounded-xs border border-error bg-error/5 px-4 py-3 text-sm text-error"
const claseCampo = "flex flex-col gap-2 text-sm font-semibold"
const claseControl =
  "min-h-11 rounded-xs border border-gray-300 bg-white px-3 py-2 font-normal hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco"

type ModalCorreccionCambioProps = {
  cambio: CambioEstado
  onCerrar: () => void
}

export const ModalCorreccionCambio = ({ cambio, onCerrar }: ModalCorreccionCambioProps) => {
  const tituloId = useId()
  const dialogo = useRef<HTMLDialogElement>(null)
  const enviando = useRef(false)
  const queryClient = useQueryClient()
  const [observaciones, setObservaciones] = useState(cambio.observaciones)
  const [motivo, setMotivo] = useState("")
  const [informe, setInforme] = useState<File | null>(null)
  const [quitarInforme, setQuitarInforme] = useState(false)
  const [fallo, setFallo] = useState<{ mensaje: string; terminal: boolean } | null>(null)
  const fueraDeServicio = cambio.estado_nuevo === "FUERA_DE_SERVICIO"
  const observacion = ultimaObservacionCambio(cambio)
  const { mutate, isPending } = useMutation({
    mutationFn: (datos: RectificacionCambioCreate) => rectificarCambio(cambio.id, datos),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cambios-observados"] })
      queryClient.invalidateQueries({ queryKey: ["bandeja"] })
      queryClient.invalidateQueries({ queryKey: ["historial", cambio.bien.id] })
      dialogo.current?.close()
    },
    onError: (e) => {
      const status = e instanceof ErrorHttp ? e.status : 0
      const terminal = status === 403 || status === 404
      if (terminal || status === 409)
        queryClient.invalidateQueries({ queryKey: ["cambios-observados"] })
      setFallo({ mensaje: e.message, terminal })
    },
    onSettled: () => {
      enviando.current = false
    },
  })
  const descarga = useMutation({
    mutationFn: async () =>
      descargarPdf(
        await obtenerInforme(cambio.id),
        cambio.informe?.nombre_original ?? "informe.pdf",
      ),
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

  const completo = !!observaciones.trim() && !!motivo.trim()

  const handleEnviar = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (enviando.current || !completo) return
    enviando.current = true
    setFallo(null)
    mutate({
      version: cambio.version_vigente,
      observaciones: observaciones.trim(),
      motivo: motivo.trim(),
      informe: quitarInforme ? null : informe,
      quitarInforme,
    })
  }

  return (
    <dialog
      ref={dialogo}
      onCancel={(e) => {
        if (isPending) e.preventDefault()
      }}
      onClose={onCerrar}
      aria-labelledby={tituloId}
      className="m-auto w-full max-w-2xl rounded-xs p-0 text-gray-900 shadow-xl backdrop:bg-gray-900/45"
    >
      <form onSubmit={handleEnviar} className="flex max-h-[90vh] flex-col">
        <header className="flex flex-col gap-1 border-b border-gray-200 px-6 py-4">
          <h2 id={tituloId} className="text-lg font-semibold">
            Corregir el cambio de estado de{" "}
            <span className="font-mono">{cambio.bien.identificacion}</span>
          </h2>
          <p className="text-sm text-gray-600">
            {nombreEstadoOperativo[cambio.estado_anterior]} pasa a{" "}
            {nombreEstadoOperativo[cambio.estado_nuevo]}. Corregí lo observado y mandalo de nuevo a
            revisión. El estado del bien no cambia.
          </p>
        </header>
        {fallo && (
          <div role="alert" className={`mx-6 mt-4 ${claseError} font-medium`}>
            {fallo.mensaje}
          </div>
        )}
        <div className="overflow-y-auto px-6 py-4">
          <fieldset
            disabled={isPending || !!fallo?.terminal}
            className="flex min-w-0 flex-col gap-4"
          >
            {observacion && (
              <p className="rounded-xs border border-error bg-error/5 px-4 py-3 text-sm text-red-900">
                <span className="font-semibold">Observado</span> por{" "}
                <span className="font-mono">{observacion.usuario}</span> el{" "}
                <span className="font-mono">{fechaHoraLegible(observacion.fecha)}</span>
                {observacion.motivo_observacion && `: ${observacion.motivo_observacion}`}
              </p>
            )}
            <HistorialActa
              eventos={historialCambio(cambio).filter(
                (evento) => evento.fecha !== observacion?.fecha,
              )}
            />
            <label className={claseCampo}>
              Observaciones
              <textarea
                required
                maxLength={500}
                rows={3}
                value={observaciones}
                onChange={(e) => setObservaciones(e.target.value)}
                className={claseControl}
              />
            </label>
            <div className="flex flex-col gap-2 text-sm">
              <span className="font-semibold">Informe vigente</span>
              {cambio.informe ? (
                <button
                  type="button"
                  disabled={descarga.isPending}
                  onClick={() => descarga.mutate()}
                  className="w-fit font-semibold text-marca underline hover:text-marca-hover focus-visible:outline-3 focus-visible:outline-foco disabled:opacity-50"
                >
                  {descarga.isPending ? "Descargando…" : cambio.informe.nombre_original}
                </button>
              ) : (
                <span className="text-gray-500">Sin informe</span>
              )}
              {descarga.error && (
                <p role="alert" className={claseError}>
                  {descarga.error.message}
                </p>
              )}
            </div>
            {!fueraDeServicio && cambio.informe && (
              <label className="flex items-center gap-2 text-sm font-semibold">
                <input
                  type="checkbox"
                  checked={quitarInforme}
                  onChange={(e) => setQuitarInforme(e.target.checked)}
                  className="size-4"
                />
                Quitar el informe
              </label>
            )}
            <CampoPdf
              etiqueta={cambio.informe ? "Reemplazar el informe" : "Sumar un informe"}
              ayuda={
                fueraDeServicio
                  ? "Opcional. Si no elegís otro, se conserva el informe vigente."
                  : "Opcional. PDF de hasta 10 MB. No se puede combinar con quitar el informe."
              }
              deshabilitado={isPending || quitarInforme}
              onElegir={setInforme}
            />
            <label className={claseCampo}>
              Motivo de la corrección
              <textarea
                required
                maxLength={500}
                rows={2}
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                className={claseControl}
              />
              <span className="text-xs font-normal text-gray-500">
                Obligatorio. Contá qué corregiste y por qué.
              </span>
            </label>
          </fieldset>
        </div>
        <footer className="flex justify-end gap-2 border-t border-gray-200 px-6 py-3">
          {fallo?.terminal ? (
            <Boton type="button" onClick={onCerrar}>
              Volver a la lista
            </Boton>
          ) : (
            <>
              <Boton type="button" variant="contorno" onClick={onCerrar} disabled={isPending}>
                Cancelar
              </Boton>
              <Boton type="submit" disabled={!completo || isPending}>
                {isPending ? "Enviando…" : "Enviar a revisión"}
              </Boton>
            </>
          )}
        </footer>
      </form>
    </dialog>
  )
}
