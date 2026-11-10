import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useId, useRef, useState, type ReactNode } from "react"
import { obtenerCambio, obtenerInforme, revisarCambio } from "../api/cambiosEstado"
import { ErrorHttp } from "../api/http"
import { nombreEstadoOperativo, tiposDeBien } from "../tipos/bien"
import { historialCambio, type CambioEstado } from "../tipos/cambioEstado"
import { descargarPdf } from "../tipos/documento"
import { fechaHoraLegible } from "../tipos/movimiento"
import type { RevisionCreate } from "../tipos/revision"
import { Boton } from "./Boton"
import { HistorialActa } from "./HistorialActa"

const claseError = "rounded-xs border border-error bg-error/5 px-4 py-3 text-sm text-error"

const Fila = ({ etiqueta, children }: { etiqueta: string; children: ReactNode }) => (
  <>
    <dt className="pt-2 font-etiqueta text-xs font-semibold tracking-wider text-gray-500 uppercase sm:pt-0.5">
      {etiqueta}
    </dt>
    <dd>{children}</dd>
  </>
)

type ModalRevisionCambioProps = {
  cambioId: number
  onCerrar: () => void
  onTerminada: () => void
}

export const ModalRevisionCambio = ({
  cambioId,
  onCerrar,
  onTerminada,
}: ModalRevisionCambioProps) => {
  const tituloId = useId()
  const dialogo = useRef<HTMLDialogElement>(null)
  const campoMotivo = useRef<HTMLTextAreaElement>(null)
  const enviando = useRef(false)
  const queryClient = useQueryClient()
  const [observando, setObservando] = useState(false)
  const [motivo, setMotivo] = useState("")
  const [fallo, setFallo] = useState<string | null>(null)
  const {
    data: cambio,
    isPending: cargando,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["cambio", cambioId],
    queryFn: () => obtenerCambio(cambioId),
    gcTime: 0,
    retry: false,
    refetchOnWindowFocus: false,
  })
  const revision = useMutation({
    mutationFn: (datos: RevisionCreate) => revisarCambio(cambioId, datos),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bandeja"] })
      if (cambio) queryClient.invalidateQueries({ queryKey: ["historial", cambio.bien.id] })
      onTerminada()
    },
    onError: (e) => {
      setFallo(e.message)
      if (e instanceof ErrorHttp && [403, 404, 409].includes(e.status)) {
        queryClient.invalidateQueries({ queryKey: ["bandeja"] })
        refetch()
      }
    },
    onSettled: () => {
      enviando.current = false
    },
  })
  const descarga = useMutation({
    mutationFn: async (actual: CambioEstado) =>
      descargarPdf(
        await obtenerInforme(actual.id),
        actual.informe?.nombre_original ?? "informe.pdf",
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

  useEffect(() => {
    if (observando) campoMotivo.current?.focus()
  }, [observando])

  const enviar = (datos: RevisionCreate) => {
    if (enviando.current) return
    enviando.current = true
    setFallo(null)
    revision.mutate(datos)
  }

  const pendiente = cambio?.estado === "APLICADO" && cambio.estado_revision === "PENDIENTE"

  const cuerpo = () => {
    if (cargando)
      return (
        <p role="status" className="text-sm text-gray-600">
          Cargando el cambio de estado…
        </p>
      )
    if (isError)
      return (
        <div role="alert" className={claseError}>
          <p>{error.message}</p>
        </div>
      )
    return (
      <>
        <dl className="grid gap-x-4 gap-y-1 text-sm sm:grid-cols-[10rem_1fr]">
          <Fila etiqueta="Bien">
            <span className="font-mono">{cambio.bien.identificacion}</span> · {cambio.bien.marca}{" "}
            {cambio.bien.modelo} · {tiposDeBien[cambio.bien.tipo_bien] ?? cambio.bien.tipo_bien}
          </Fila>
          <Fila etiqueta="Registró">
            {cambio.unidad_registrante} · <span className="font-mono">{cambio.usuario}</span> el{" "}
            <span className="font-mono">{fechaHoraLegible(cambio.fecha)}</span>
          </Fila>
          <Fila etiqueta="Estado">
            {nombreEstadoOperativo[cambio.estado_anterior]} pasa a{" "}
            <span className="font-semibold">{nombreEstadoOperativo[cambio.estado_nuevo]}</span>
          </Fila>
          <Fila etiqueta="Observaciones">{cambio.observaciones}</Fila>
          <Fila etiqueta="Informe">
            {cambio.informe ? (
              <button
                type="button"
                disabled={descarga.isPending}
                onClick={() => descarga.mutate(cambio)}
                className="font-semibold text-marca underline hover:text-marca-hover focus-visible:outline-3 focus-visible:outline-foco disabled:opacity-50"
              >
                {descarga.isPending ? "Descargando…" : cambio.informe.nombre_original}
              </button>
            ) : (
              <span className="text-gray-500">Sin informe</span>
            )}
          </Fila>
        </dl>
        {descarga.error && (
          <p role="alert" className={claseError}>
            {descarga.error.message}
          </p>
        )}
        <HistorialActa eventos={historialCambio(cambio)} />
        {!pendiente && (
          <p role="status" className="text-sm font-semibold text-gray-700">
            Este cambio ya no está pendiente de revisión.
          </p>
        )}
        {observando && pendiente && (
          <label className="flex flex-col gap-2 text-sm font-semibold">
            Motivo de la observación
            <textarea
              ref={campoMotivo}
              required
              maxLength={500}
              rows={3}
              value={motivo}
              disabled={revision.isPending}
              onChange={(e) => setMotivo(e.target.value)}
              className="min-h-11 rounded-xs border border-gray-300 bg-white px-3 py-2 font-normal hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco"
            />
            <span className="text-xs font-normal text-gray-500">
              Obligatorio. La unidad lo va a ver para corregirlo.
            </span>
          </label>
        )}
      </>
    )
  }

  const acciones = () => {
    if (!cambio || !pendiente)
      return (
        <Boton type="button" onClick={onCerrar}>
          Cerrar
        </Boton>
      )
    const version = cambio.version_vigente
    if (observando)
      return (
        <>
          <Boton
            type="button"
            variant="contorno"
            disabled={revision.isPending}
            onClick={() => setObservando(false)}
          >
            Volver
          </Boton>
          <Boton
            type="button"
            disabled={!motivo.trim() || revision.isPending}
            onClick={() =>
              enviar({ resultado: "OBSERVADO", motivo_observacion: motivo.trim(), version })
            }
          >
            {revision.isPending ? "Enviando…" : "Enviar observación"}
          </Boton>
        </>
      )
    return (
      <>
        <Boton type="button" variant="contorno" onClick={onCerrar} disabled={revision.isPending}>
          Cerrar
        </Boton>
        <Boton
          type="button"
          variant="peligro"
          onClick={() => setObservando(true)}
          disabled={revision.isPending}
        >
          Observar
        </Boton>
        <Boton
          type="button"
          onClick={() => enviar({ resultado: "REVISADO", version })}
          disabled={revision.isPending}
        >
          {revision.isPending ? "Confirmando…" : "Confirmar"}
        </Boton>
      </>
    )
  }

  return (
    <dialog
      ref={dialogo}
      onCancel={(e) => {
        if (revision.isPending) e.preventDefault()
      }}
      onClose={onCerrar}
      aria-labelledby={tituloId}
      className="m-auto w-full max-w-2xl rounded-xs p-0 text-gray-900 shadow-xl backdrop:bg-gray-900/45"
    >
      <div className="flex max-h-[90vh] flex-col">
        <header className="border-b border-gray-200 px-6 py-4">
          <h2 id={tituloId} className="text-lg font-semibold">
            Revisar cambio de estado
            {cambio && (
              <>
                {" "}
                de <span className="font-mono">{cambio.bien.identificacion}</span>
              </>
            )}
          </h2>
          <p className="text-sm text-gray-600">
            Abrí el informe y confirmá el cambio, u observalo si encontrás algo mal.
          </p>
        </header>
        {fallo && (
          <div role="alert" className={`mx-6 mt-4 ${claseError} font-medium`}>
            {fallo}
          </div>
        )}
        <div className="flex flex-col gap-4 overflow-y-auto px-6 py-4">{cuerpo()}</div>
        <footer className="flex justify-end gap-2 border-t border-gray-200 px-6 py-3">
          {acciones()}
        </footer>
      </div>
    </dialog>
  )
}
