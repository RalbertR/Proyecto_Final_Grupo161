import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef, useState, type FormEvent } from "react"
import { ErrorHttp } from "../api/http"
import { recibirEntrega } from "../api/movimientos"
import { obtenerUbicaciones } from "../api/unidades"
import {
  fechaLegible,
  motivoInicial,
  ubicacionPorDefecto,
  type ControlActa,
  type ControlBien,
  type Movimiento,
  type Recepcion,
} from "../tipos/movimiento"
import { Boton } from "./Boton"
import { ResumenRecepcion } from "./ResumenRecepcion"
import { TablaControl } from "./TablaControl"

const claseAviso = "mx-6 shrink-0 rounded-xs border px-4 py-3 text-sm font-medium"

type ModalRecepcionProps = {
  acta: Movimiento
  control: ControlActa
  onCambiar: (bienId: number, cambio: Partial<ControlBien>) => void
  onCerrar: () => void
  onTerminada: () => void
}

export const ModalRecepcion = ({
  acta,
  control,
  onCambiar,
  onCerrar,
  onTerminada,
}: ModalRecepcionProps) => {
  const dialogo = useRef<HTMLDialogElement>(null)
  const enviando = useRef(false)
  const queryClient = useQueryClient()
  const [rechazando, setRechazando] = useState(false)
  const [motivo, setMotivo] = useState("")
  const { data: ubicaciones, isError: sinUbicaciones } = useQuery({
    queryKey: ["ubicaciones"],
    queryFn: obtenerUbicaciones,
    retry: false,
  })
  const {
    mutate,
    isPending,
    isError,
    error,
    data: recibida,
    reset,
  } = useMutation({
    mutationFn: (recepcion: Recepcion) => recibirEntrega(acta.id, recepcion),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["por-recibir"] })
      queryClient.invalidateQueries({ queryKey: ["inventario"] })
    },
    onError: (e) => {
      if (e instanceof ErrorHttp && (e.status === 404 || e.status === 409))
        queryClient.invalidateQueries({ queryKey: ["por-recibir"] })
    },
    onSettled: () => {
      enviando.current = false
    },
  })

  useEffect(() => {
    const d = dialogo.current
    if (d && !d.open) d.showModal()
  }, [])

  const yaRecibida =
    isError && error instanceof ErrorHttp && (error.status === 404 || error.status === 409)
  const total = acta.bienes.length
  const controlados = acta.bienes.filter((b) => control[b.bien_id]?.controlado).length
  const conNovedad = acta.bienes.filter((b) => control[b.bien_id]?.conNovedad).length
  const ubicacionesElegidas = acta.bienes.flatMap((b) => {
    const id =
      control[b.bien_id]?.ubicacionId ??
      (ubicaciones ? ubicacionPorDefecto(b.tipo_bien, ubicaciones) : undefined)
    return id === undefined ? [] : [{ bien_id: b.bien_id, ubicacion_id: id }]
  })
  const puedeAceptar =
    !!ubicaciones &&
    controlados === total &&
    conNovedad === 0 &&
    ubicacionesElegidas.length === total

  const enviar = (recepcion: Recepcion) => {
    if (enviando.current) return
    enviando.current = true
    mutate(recepcion)
  }

  const handleAceptar = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!puedeAceptar) return
    enviar({ resultado: "ACEPTADO", ubicaciones: ubicacionesElegidas })
  }

  const handleRechazar = () => {
    reset()
    setMotivo(motivoInicial(acta.bienes, control))
    setRechazando(true)
  }

  const handleVolver = () => {
    reset()
    setRechazando(false)
  }

  const handleConfirmarRechazo = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const texto = motivo.trim()
    if (!texto) return
    enviar({ resultado: "RECHAZADO", motivo_rechazo: texto })
  }

  const avisoError = isError && (
    <div role="alert" className={`${claseAviso} mt-4 border-error bg-error/5 text-error`}>
      {error.message}
    </div>
  )

  const volverALista = (
    <Boton type="button" onClick={onTerminada} className="ml-auto">
      Volver a la lista
    </Boton>
  )

  return (
    <dialog
      ref={dialogo}
      onCancel={(e) => {
        if (isPending) e.preventDefault()
      }}
      onClose={recibida || yaRecibida ? onTerminada : onCerrar}
      aria-labelledby="titulo-recepcion"
      className="m-auto w-full max-w-5xl rounded-xs p-0 text-gray-900 shadow-xl backdrop:bg-gray-900/45"
    >
      {recibida ? (
        <div className="flex max-h-[90vh] flex-col">
          <header className="border-b border-gray-200 px-6 py-4">
            <h2 id="titulo-recepcion" className="text-lg font-semibold">
              {recibida.estado === "APLICADO" ? "Acta recibida" : "Acta rechazada"}
            </h2>
          </header>
          <div className="overflow-y-auto px-6 py-4">
            <ResumenRecepcion movimiento={recibida} />
          </div>
          <footer className="flex justify-end border-t border-gray-200 px-6 py-3">
            <Boton onClick={onTerminada}>Volver a la lista</Boton>
          </footer>
        </div>
      ) : rechazando ? (
        <form onSubmit={handleConfirmarRechazo} className="flex max-h-[90vh] flex-col">
          <header className="flex items-baseline justify-between gap-4 border-b border-gray-200 px-6 py-4">
            <h2 id="titulo-recepcion" className="text-lg font-semibold">
              Rechazar acta <span className="font-mono">{acta.numero_acta}</span>
            </h2>
            <span className="text-sm text-gray-500">A {acta.unidad_origen?.nombre}</span>
          </header>
          {avisoError}
          <div className="overflow-y-auto px-6 py-4">
            <fieldset disabled={isPending || yaRecibida} className="min-w-0">
              <label className="flex flex-col gap-2 text-sm font-semibold">
                Motivo
                <textarea
                  required
                  autoFocus
                  maxLength={500}
                  rows={4}
                  value={motivo}
                  onChange={(e) => setMotivo(e.target.value)}
                  onFocus={(e) => {
                    const fin = e.currentTarget.value.length
                    e.currentTarget.setSelectionRange(fin, fin)
                  }}
                  className="min-h-11 rounded-xs border border-gray-300 bg-white px-3 py-2 font-normal hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco"
                />
                <span className="text-xs font-normal text-gray-500">
                  Contá qué no coincide con el acta en papel, hasta 500 caracteres
                </span>
              </label>
            </fieldset>
          </div>
          <footer className="flex justify-end gap-2 border-t border-gray-200 px-6 py-3">
            {yaRecibida ? (
              volverALista
            ) : (
              <>
                <Boton type="button" variant="contorno" onClick={handleVolver} disabled={isPending}>
                  Volver
                </Boton>
                <Boton type="submit" variant="peligro" disabled={isPending || !motivo.trim()}>
                  {isPending ? "Rechazando…" : "Confirmar rechazo"}
                </Boton>
              </>
            )}
          </footer>
        </form>
      ) : (
        <form onSubmit={handleAceptar} className="flex max-h-[90vh] flex-col">
          <header className="flex items-baseline justify-between gap-4 border-b border-gray-200 px-6 py-4">
            <h2 id="titulo-recepcion" className="text-lg font-semibold">
              Recibir acta <span className="font-mono">{acta.numero_acta}</span>
            </h2>
            <span className="text-sm text-gray-500">Desde {acta.unidad_origen?.nombre}</span>
          </header>
          {avisoError}
          {sinUbicaciones && (
            <div role="alert" className={`${claseAviso} mt-4 border-error bg-error/5 text-error`}>
              No se pudieron cargar las ubicaciones
            </div>
          )}
          <div className="overflow-y-auto px-6 py-4">
            <fieldset disabled={isPending || yaRecibida} className="flex min-w-0 flex-col gap-4">
              <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 text-sm">
                <dt className="font-semibold">Fecha del hecho</dt>
                <dd className="font-mono">{fechaLegible(acta.fecha_hecho)}</dd>
                <dt className="font-semibold">Cargada por</dt>
                <dd className="font-mono">{acta.usuario}</dd>
                {acta.descripcion && (
                  <>
                    <dt className="font-semibold">Descripción</dt>
                    <dd>{acta.descripcion}</dd>
                  </>
                )}
              </dl>
              <TablaControl
                bienes={acta.bienes}
                control={control}
                ubicaciones={ubicaciones ?? []}
                onCambiar={onCambiar}
              />
            </fieldset>
          </div>
          {conNovedad > 0 && !yaRecibida && (
            <div className={`${claseAviso} mb-3 border-pendiente bg-pendiente/10 text-amber-900`}>
              Hay un bien con novedad. Para corregirlo, rechazá el acta a la unidad de origen.
            </div>
          )}
          <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-gray-200 px-6 py-3">
            {yaRecibida ? (
              volverALista
            ) : (
              <>
                <span className="text-sm text-gray-600">
                  {controlados} de {total} controlados
                  {conNovedad > 0 && ` · ${conNovedad} con novedad`}
                </span>
                <div className="flex gap-2">
                  <Boton type="button" variant="contorno" onClick={onCerrar} disabled={isPending}>
                    Cancelar
                  </Boton>
                  <Boton
                    type="button"
                    variant="peligro"
                    onClick={handleRechazar}
                    disabled={isPending}
                  >
                    Rechazar
                  </Boton>
                  <Boton type="submit" disabled={isPending || !puedeAceptar}>
                    {isPending ? "Aceptando…" : "Aceptar"}
                  </Boton>
                </div>
              </>
            )}
          </footer>
        </form>
      )}
    </dialog>
  )
}
