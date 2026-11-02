import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef, useState, type FormEvent } from "react"
import { ErrorHttp } from "../api/http"
import { obtenerMovimiento } from "../api/movimientos"
import { revisarMovimiento } from "../api/revisiones"
import {
  controlVigente,
  datosActa,
  type ControlRevision,
  type RevisionCreate,
} from "../tipos/revision"
import { Boton } from "./Boton"
import { DatosRevision } from "./DatosRevision"
import { HistorialActa } from "./HistorialActa"
import { Marca } from "./Marca"
import { TablaRevision } from "./TablaRevision"

const claseAviso = "mx-6 mt-4 shrink-0 rounded-xs border px-4 py-3 text-sm font-medium"

type Fallo = { mensaje: string; terminal: boolean }

type ModalRevisionProps = {
  movimientoId: number
  control: ControlRevision | undefined
  onCambiar: (control: ControlRevision) => void
  onCerrar: () => void
  onTerminada: () => void
}

export const ModalRevision = ({
  movimientoId,
  control: controlGuardado,
  onCambiar,
  onCerrar,
  onTerminada,
}: ModalRevisionProps) => {
  const dialogo = useRef<HTMLDialogElement>(null)
  const enviando = useRef(false)
  const queryClient = useQueryClient()
  const [fallo, setFallo] = useState<Fallo | null>(null)
  const [corregida, setCorregida] = useState(false)
  const {
    data: acta,
    isError: sinDetalle,
    error: errorDetalle,
    refetch,
  } = useQuery({
    queryKey: ["movimiento", movimientoId],
    queryFn: () => obtenerMovimiento(movimientoId),
    retry: false,
    refetchOnWindowFocus: false,
    gcTime: 0,
  })
  const {
    mutate,
    isPending,
    data: revisada,
  } = useMutation({
    mutationFn: (revision: RevisionCreate) => revisarMovimiento(movimientoId, revision),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bandeja"] })
    },
    onError: async (e, revision) => {
      const status = e instanceof ErrorHttp ? e.status : 0
      if (status === 403 || status === 404) {
        queryClient.invalidateQueries({ queryKey: ["bandeja"] })
        setFallo({ mensaje: e.message, terminal: true })
        return
      }
      if (status === 409) {
        queryClient.invalidateQueries({ queryKey: ["bandeja"] })
        const { data: nuevo } = await refetch()
        if (nuevo?.estado_revision === "PENDIENTE" && nuevo.version_vigente !== revision.version) {
          setCorregida(true)
          return
        }
        if (nuevo && nuevo.estado_revision !== "PENDIENTE") {
          setFallo({ mensaje: e.message, terminal: true })
          return
        }
      }
      setFallo({ mensaje: e.message, terminal: false })
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

  const terminada = !!revisada || !!fallo?.terminal

  const enviar = (revision: RevisionCreate) => {
    if (enviando.current) return
    enviando.current = true
    setFallo(null)
    setCorregida(false)
    mutate(revision)
  }

  const volverALista = (
    <Boton type="button" onClick={onTerminada} className="ml-auto">
      Volver a la lista
    </Boton>
  )

  const contenido = () => {
    if (revisada)
      return (
        <div className="flex max-h-[90vh] flex-col">
          <header className="border-b border-gray-200 px-6 py-4">
            <h2 id="titulo-revision" className="text-lg font-semibold">
              {revisada.resultado === "OBSERVADO" ? "Acta observada" : "Acta revisada"}
            </h2>
          </header>
          <div className="flex flex-col gap-4 overflow-y-auto px-6 py-4">
            <p
              role="status"
              className="rounded-xs border border-exito bg-exito/5 px-4 py-3 text-sm font-semibold text-green-900"
            >
              {revisada.resultado === "OBSERVADO"
                ? "La unidad que lo registró lo va a ver para corregirlo."
                : "El movimiento quedó revisado."}
            </p>
            {revisada.motivo_observacion && (
              <p className="text-sm">
                <span className="font-semibold">Motivo:</span> {revisada.motivo_observacion}
              </p>
            )}
          </div>
          <footer className="flex justify-end border-t border-gray-200 px-6 py-3">
            {volverALista}
          </footer>
        </div>
      )

    if (!acta)
      return (
        <div className="flex max-h-[90vh] flex-col">
          <header className="border-b border-gray-200 px-6 py-4">
            <h2 id="titulo-revision" className="text-lg font-semibold">
              Revisar acta
            </h2>
          </header>
          <div className="px-6 py-4">
            {sinDetalle ? (
              <div role="alert" className="space-y-3 rounded-xs border border-error p-4 text-error">
                <p>{errorDetalle.message}</p>
                <Boton variant="contorno" onClick={() => refetch()}>
                  Reintentar
                </Boton>
              </div>
            ) : (
              <div aria-busy="true" className="space-y-2">
                {[1, 2, 3, 4].map((n) => (
                  <div key={n} className="h-10 animate-pulse rounded-xs bg-gray-200" />
                ))}
              </div>
            )}
          </div>
          <footer className="flex justify-end border-t border-gray-200 px-6 py-3">
            <Boton type="button" variant="contorno" onClick={onCerrar}>
              Cancelar
            </Boton>
          </footer>
        </div>
      )

    const control = controlVigente(controlGuardado, acta.version_vigente)
    const total = datosActa.length + acta.bienes.length
    const controlados =
      datosActa.filter((dato) => control.datos[dato]).length +
      acta.bienes.filter((bien) => control.bienes[bien.bien_id]).length
    const completo = controlados === total

    const handleRevisado = (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault()
      if (!completo) return
      enviar({ resultado: "REVISADO", version: acta.version_vigente })
    }

    return (
      <form onSubmit={handleRevisado} className="flex max-h-[90vh] flex-col">
        <header className="flex flex-col gap-1 border-b border-gray-200 px-6 py-4">
          <h2 id="titulo-revision" className="flex items-center gap-3 text-lg font-semibold">
            <span>
              Revisar acta <span className="font-mono">{acta.numero_acta}</span>
            </span>
            {acta.version_vigente > 0 && <Marca tono="secundario">Corregida</Marca>}
          </h2>
          <p className="text-sm text-gray-600">
            Compará cada dato con el acta escaneada que llegó por correo y tildá los que coinciden.
          </p>
        </header>
        {corregida && (
          <div
            role="status"
            className={`${claseAviso} border-pendiente bg-pendiente/10 text-amber-900`}
          >
            La unidad corrigió el acta mientras la revisabas. Volvé a controlarla con los datos
            nuevos.
          </div>
        )}
        {fallo && (
          <div role="alert" className={`${claseAviso} border-error bg-error/5 text-error`}>
            {fallo.mensaje}
          </div>
        )}
        <div className="overflow-y-auto px-6 py-4">
          <fieldset disabled={isPending || terminada} className="flex min-w-0 flex-col gap-4">
            <HistorialActa acta={acta} />
            <DatosRevision acta={acta} control={control} onCambiar={onCambiar} />
            <TablaRevision acta={acta} control={control} onCambiar={onCambiar} />
          </fieldset>
        </div>
        <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-gray-200 px-6 py-3">
          {terminada ? (
            volverALista
          ) : (
            <>
              <span className="text-sm text-gray-600">
                {controlados} de {total} controlados
              </span>
              <div className="flex gap-2">
                <Boton type="button" variant="contorno" onClick={onCerrar} disabled={isPending}>
                  Cancelar
                </Boton>
                <Boton type="button" variant="peligro" disabled={isPending}>
                  Observar
                </Boton>
                <Boton type="submit" disabled={isPending || !completo}>
                  {isPending ? "Enviando…" : "Revisado"}
                </Boton>
              </div>
            </>
          )}
        </footer>
      </form>
    )
  }

  return (
    <dialog
      ref={dialogo}
      onCancel={(e) => {
        if (isPending) e.preventDefault()
      }}
      onClose={terminada ? onTerminada : onCerrar}
      aria-labelledby="titulo-revision"
      className="m-auto w-full max-w-5xl rounded-xs p-0 text-gray-900 shadow-xl backdrop:bg-gray-900/45"
    >
      {contenido()}
    </dialog>
  )
}
