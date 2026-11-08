import { useMutation, useQueryClient } from "@tanstack/react-query"
import {
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
  type ReactNode,
} from "react"
import { ErrorHttp } from "../api/http"
import { rectificarMovimiento } from "../api/movimientos"
import {
  fechaHoraLegible,
  fechaLegible,
  hoy,
  ultimaObservacion,
  type Movimiento,
  type RectificacionCreate,
} from "../tipos/movimiento"
import { extremosDelActa, historialActa, nombreDelActa } from "../tipos/revision"
import { BienesActa } from "./BienesActa"
import { Boton } from "./Boton"
import { HistorialActa } from "./HistorialActa"

const claseAviso = "mx-6 mt-4 shrink-0 rounded-xs border px-4 py-3 text-sm font-medium"
const claseCampo = "flex flex-col gap-2 text-sm font-semibold"
const claseControl =
  "min-h-11 rounded-xs border bg-white px-3 py-2 font-normal hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco"
const claseBorde = (cambiado: boolean) => (cambiado ? "border-pendiente" : "border-gray-300")

type Fallo = { mensaje: string; terminal: boolean }

const Antes = ({ children }: { children: ReactNode }) => (
  <span className="text-xs font-normal text-gray-500">Antes: {children}</span>
)

type ModalRectificacionProps = {
  acta: Movimiento
  onCerrar: () => void
}

export const ModalRectificacion = ({ acta, onCerrar }: ModalRectificacionProps) => {
  const dialogo = useRef<HTMLDialogElement>(null)
  const campoMotivo = useRef<HTMLTextAreaElement>(null)
  const enviando = useRef(false)
  const queryClient = useQueryClient()
  const [fallo, setFallo] = useState<Fallo | null>(null)
  const [faltaMotivo, setFaltaMotivo] = useState(false)
  const [datos, setDatos] = useState({
    numeroActa: acta.numero_acta ?? "",
    fechaHecho: acta.fecha_hecho,
    descripcion: acta.descripcion ?? "",
    motivo: "",
  })
  const {
    mutate,
    isPending,
    data: corregida,
    variables,
  } = useMutation({
    mutationFn: (rectificacion: RectificacionCreate) =>
      rectificarMovimiento(acta.id, rectificacion),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["observados"] })
      queryClient.invalidateQueries({ queryKey: ["movimiento", acta.id] })
      queryClient.invalidateQueries({ queryKey: ["bandeja"] })
    },
    onError: (e) => {
      const status = e instanceof ErrorHttp ? e.status : 0
      const terminal = status === 403 || status === 404 || status === 409
      if (terminal) queryClient.invalidateQueries({ queryKey: ["observados"] })
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

  const terminada = !!corregida || !!fallo?.terminal
  const observacion = ultimaObservacion(acta)
  const { origen, destino } = extremosDelActa(acta)
  const movimiento = `${nombreDelActa(acta)} de ${origen}${destino ? ` a ${destino}` : ""}`
  const cambioNumero = datos.numeroActa !== (acta.numero_acta ?? "")
  const cambioFecha = datos.fechaHecho !== acta.fecha_hecho
  const cambioDescripcion = datos.descripcion.trim() !== (acta.descripcion ?? "").trim()

  const cambiar =
    (campo: keyof typeof datos) => (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setDatos((actual) => ({ ...actual, [campo]: e.target.value }))
      if (campo === "motivo") setFaltaMotivo(false)
    }

  const handleEnviar = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (enviando.current) return
    const motivo = datos.motivo.trim()
    if (!motivo) {
      setFaltaMotivo(true)
      campoMotivo.current?.focus()
      return
    }
    enviando.current = true
    setFallo(null)
    mutate({
      fecha_hecho: datos.fechaHecho,
      numero_acta: datos.numeroActa,
      descripcion: datos.descripcion.trim() || null,
      motivo,
    })
  }

  const volverALista = (
    <Boton type="button" onClick={onCerrar} className="ml-auto">
      Volver a la lista
    </Boton>
  )

  const contenido = () => {
    if (corregida)
      return (
        <div className="flex max-h-[90vh] flex-col">
          <header className="border-b border-gray-200 px-6 py-4">
            <h2 id="titulo-rectificacion" className="text-lg font-semibold">
              Acta enviada a revisión
            </h2>
          </header>
          <div className="flex flex-col gap-4 overflow-y-auto px-6 py-4">
            <p
              role="status"
              className="rounded-xs border border-exito bg-exito/5 px-4 py-3 text-sm font-semibold text-green-900"
            >
              Tu superior la va a volver a revisar.
            </p>
            <p className="text-sm">
              <span className="font-semibold">Motivo:</span> {variables?.motivo}
            </p>
          </div>
          <footer className="flex justify-end border-t border-gray-200 px-6 py-3">
            {volverALista}
          </footer>
        </div>
      )

    return (
      <form onSubmit={handleEnviar} className="flex max-h-[90vh] flex-col">
        <header className="flex flex-col gap-1 border-b border-gray-200 px-6 py-4">
          <h2 id="titulo-rectificacion" className="text-lg font-semibold">
            Corregir acta <span className="font-mono">{acta.numero_acta}</span>
          </h2>
          <p className="text-sm text-gray-600">
            Corregí los datos para que coincidan con el acta en papel. Si el acta se salvó o se
            volvió a firmar, reenviala por correo y contalo en el motivo.
          </p>
        </header>
        {fallo && (
          <div role="alert" className={`${claseAviso} border-error bg-error/5 text-error`}>
            {fallo.mensaje}
          </div>
        )}
        <div className="overflow-y-auto px-6 py-4">
          <fieldset disabled={isPending || terminada} className="flex min-w-0 flex-col gap-4">
            <HistorialActa eventos={historialActa(acta).slice(0, -1)} />
            {observacion && (
              <p className="rounded-xs border border-error bg-error/5 px-4 py-3 text-sm text-red-900">
                <span className="font-semibold">Observada</span> por{" "}
                <span className="font-mono">{observacion.usuario}</span> el{" "}
                <span className="font-mono">{fechaHoraLegible(observacion.fecha)}</span>
                {observacion.motivo_observacion && `: ${observacion.motivo_observacion}`}
              </p>
            )}
            <dl className="grid gap-x-4 gap-y-1 text-sm sm:grid-cols-[10rem_1fr]">
              <dt className="text-xs font-semibold tracking-wide text-gray-500 uppercase sm:pt-0.5">
                Movimiento
              </dt>
              <dd>{movimiento}</dd>
              <dt className="pt-2 text-xs font-semibold tracking-wide text-gray-500 uppercase sm:pt-0.5">
                Cargó
              </dt>
              <dd className="font-mono">{acta.usuario}</dd>
            </dl>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className={claseCampo}>
                Número de acta
                <input
                  required
                  pattern="[0-9]{4}/[0-9]{4}"
                  placeholder="0001/2026"
                  title="Cuatro dígitos y el año, por ejemplo 0001/2026"
                  value={datos.numeroActa}
                  onChange={cambiar("numeroActa")}
                  className={`${claseControl} ${claseBorde(cambioNumero)} font-mono`}
                />
                <span className="text-xs font-normal text-gray-500">Cuatro dígitos y el año</span>
                {cambioNumero && (
                  <Antes>
                    <span className="font-mono">{acta.numero_acta}</span>
                  </Antes>
                )}
              </label>
              <label className={claseCampo}>
                Fecha del hecho
                <input
                  type="date"
                  required
                  max={hoy()}
                  value={datos.fechaHecho}
                  onChange={cambiar("fechaHecho")}
                  className={`${claseControl} ${claseBorde(cambioFecha)} font-mono`}
                />
                {cambioFecha && (
                  <Antes>
                    <span className="font-mono">{fechaLegible(acta.fecha_hecho)}</span>
                  </Antes>
                )}
              </label>
            </div>
            <label className={claseCampo}>
              Descripción
              <textarea
                maxLength={500}
                rows={2}
                value={datos.descripcion}
                onChange={cambiar("descripcion")}
                className={`${claseControl} ${claseBorde(cambioDescripcion)}`}
              />
              {cambioDescripcion && <Antes>{acta.descripcion || "Sin descripción"}</Antes>}
            </label>
            <label className={claseCampo}>
              Motivo de la corrección
              <textarea
                ref={campoMotivo}
                maxLength={500}
                rows={3}
                aria-required="true"
                aria-invalid={faltaMotivo}
                aria-describedby={faltaMotivo ? "ayuda-motivo error-motivo" : "ayuda-motivo"}
                value={datos.motivo}
                onChange={cambiar("motivo")}
                className={`${claseControl} ${faltaMotivo ? "border-error" : "border-gray-300"}`}
              />
              <span id="ayuda-motivo" className="text-xs font-normal text-gray-500">
                Obligatorio. Contá qué corregiste y por qué.
              </span>
              {faltaMotivo && (
                <span id="error-motivo" className="text-xs font-semibold text-error">
                  Escribí el motivo de la corrección
                </span>
              )}
            </label>
            <BienesActa acta={acta} />
            <p className="-mt-2 text-xs text-gray-600">
              Los bienes y las unidades no se corrigen. Si no coinciden con el acta, el superior
              tiene que anularla.
            </p>
          </fieldset>
        </div>
        <footer className="flex justify-end gap-2 border-t border-gray-200 px-6 py-3">
          {terminada ? (
            volverALista
          ) : (
            <>
              <Boton type="button" variant="contorno" onClick={onCerrar} disabled={isPending}>
                Cancelar
              </Boton>
              <Boton type="submit" disabled={isPending}>
                {isPending ? "Enviando…" : "Enviar a revisión"}
              </Boton>
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
      onClose={onCerrar}
      aria-labelledby="titulo-rectificacion"
      className="m-auto w-full max-w-4xl rounded-xs p-0 text-gray-900 shadow-xl backdrop:bg-gray-900/45"
    >
      {contenido()}
    </dialog>
  )
}
