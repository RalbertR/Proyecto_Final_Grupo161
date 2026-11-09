import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react"
import { ErrorHttp } from "../api/http"
import { corregirEntrega, desistirDeLaEntrega } from "../api/movimientos"
import { bienDelRenglon, type BienActa } from "../tipos/bien"
import { devoluciones, hoy, type EntregaCreate, type Movimiento } from "../tipos/movimiento"
import { Boton } from "./Boton"
import { BuscadorBienes } from "./BuscadorBienes"
import { DevolucionesActa } from "./DevolucionesActa"
import { DocumentosActa } from "./DocumentosActa"
import { ListaBienesEntrega } from "./ListaBienesEntrega"
import { ResumenEntrega } from "./ResumenEntrega"

const claseCampo = "flex flex-col gap-2 text-sm font-semibold"
const claseControl =
  "min-h-11 rounded-xs border border-gray-300 bg-white px-3 py-2 font-normal hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco"
const claseError =
  "mx-6 mt-4 shrink-0 rounded-xs border border-error bg-error/5 px-4 py-3 text-sm font-medium text-error"

const sinBloqueos = new Map<number, string>()

type ModalCorreccionProps = {
  acta: Movimiento
  onCerrar: () => void
  onTerminada: () => void
}

export const ModalCorreccion = ({ acta, onCerrar, onTerminada }: ModalCorreccionProps) => {
  const dialogo = useRef<HTMLDialogElement>(null)
  const enviando = useRef(false)
  const queryClient = useQueryClient()
  const [bienes, setBienes] = useState<BienActa[]>(() => acta.bienes.map(bienDelRenglon))
  const [datos, setDatos] = useState({
    numeroActa: acta.numero_acta ?? "",
    fechaHecho: acta.fecha_hecho,
    descripcion: acta.descripcion ?? "",
  })
  const [desistiendo, setDesistiendo] = useState(false)
  const [motivo, setMotivo] = useState("")
  const conNovedad = new Set(devoluciones(acta)[0]?.bienes_con_novedad.map((n) => n.bien_id))
  const propios = new Set(acta.bienes.map((b) => b.bien_id))
  const unidadOrigenId = acta.unidad_origen?.id

  const alResolver = {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["devueltas"] })
      queryClient.invalidateQueries({ queryKey: ["inventario"] })
    },
    onError: (e: Error) => {
      if (e instanceof ErrorHttp && (e.status === 404 || e.status === 409))
        queryClient.invalidateQueries({ queryKey: ["devueltas"] })
    },
    onSettled: () => {
      enviando.current = false
    },
  }
  const correccion = useMutation({
    mutationFn: (entrega: EntregaCreate) => corregirEntrega(acta.id, entrega),
    ...alResolver,
  })
  const desistimiento = useMutation({
    mutationFn: (texto: string) => desistirDeLaEntrega(acta.id, texto),
    ...alResolver,
  })
  const isPending = correccion.isPending || desistimiento.isPending
  const error = desistiendo ? desistimiento.error : correccion.error

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

  const cambiar =
    (campo: keyof typeof datos) => (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setDatos((actual) => ({ ...actual, [campo]: e.target.value }))

  const handleQuitar = (bienId: number) =>
    setBienes((actuales) => actuales.filter((b) => b.bien_id !== bienId))

  const handleReenviar = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const destinoId = acta.unidad_destino?.id
    if (enviando.current || bienes.length === 0 || destinoId === undefined) return
    enviando.current = true
    correccion.mutate({
      unidad_destino_id: destinoId,
      numero_acta: datos.numeroActa,
      fecha_hecho: datos.fechaHecho,
      descripcion: datos.descripcion.trim() || null,
      bienes: bienes.map((b) => b.bien_id),
    })
  }

  const handleDesistir = () => {
    correccion.reset()
    setDesistiendo(true)
  }

  const handleVolver = () => {
    desistimiento.reset()
    setDesistiendo(false)
  }

  const handleConfirmarDesistimiento = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const texto = motivo.trim()
    if (enviando.current || !texto) return
    enviando.current = true
    desistimiento.mutate(texto)
  }

  const terminada = correccion.data ?? desistimiento.data

  const avisoError = error && (
    <div role="alert" className={claseError}>
      {error.message}
    </div>
  )

  const volverALista = (
    <footer className="flex justify-end border-t border-gray-200 px-6 py-3">
      <Boton onClick={onTerminada}>Volver a la lista</Boton>
    </footer>
  )

  const encabezado = (titulo: string) => (
    <header className="flex items-baseline justify-between gap-4 border-b border-gray-200 px-6 py-4">
      <h2 id="titulo-correccion" className="text-lg font-semibold">
        {titulo} <span className="font-mono">{acta.numero_acta}</span>
      </h2>
      <span className="text-sm text-gray-500">A {acta.unidad_destino?.nombre}</span>
    </header>
  )

  return (
    <dialog
      ref={dialogo}
      onCancel={(e) => {
        if (isPending) e.preventDefault()
      }}
      onClose={terminada ? onTerminada : onCerrar}
      aria-labelledby="titulo-correccion"
      className="m-auto w-full max-w-2xl rounded-xs p-0 text-gray-900 shadow-xl backdrop:bg-gray-900/45"
    >
      {correccion.data ? (
        <div className="flex max-h-[90vh] flex-col">
          <header className="border-b border-gray-200 px-6 py-4">
            <h2 id="titulo-correccion" className="text-lg font-semibold">
              Acta reenviada
            </h2>
          </header>
          <div className="overflow-y-auto px-6 py-4">
            <ResumenEntrega movimiento={correccion.data} />
          </div>
          {volverALista}
        </div>
      ) : desistimiento.data ? (
        <div className="flex max-h-[90vh] flex-col">
          <header className="border-b border-gray-200 px-6 py-4">
            <h2 id="titulo-correccion" className="text-lg font-semibold">
              Acta desistida
            </h2>
          </header>
          <div className="px-6 py-4">
            <p
              role="status"
              className="rounded-xs border border-exito bg-exito/5 px-4 py-3 text-sm font-semibold text-green-900"
            >
              Sus bienes quedaron libres en el inventario.
            </p>
          </div>
          {volverALista}
        </div>
      ) : desistiendo ? (
        <form onSubmit={handleConfirmarDesistimiento} className="flex max-h-[90vh] flex-col">
          {encabezado("Desistir del acta")}
          {avisoError}
          <div className="overflow-y-auto px-6 py-4">
            <fieldset disabled={isPending} className="min-w-0">
              <label className={claseCampo}>
                Motivo
                <textarea
                  required
                  autoFocus
                  maxLength={500}
                  rows={4}
                  value={motivo}
                  onChange={(e) => setMotivo(e.target.value)}
                  className={claseControl}
                />
                <span className="text-xs font-normal text-gray-500">
                  Contá por qué no se reenvía, hasta 500 caracteres
                </span>
              </label>
            </fieldset>
          </div>
          <footer className="flex justify-end gap-2 border-t border-gray-200 px-6 py-3">
            <Boton type="button" variant="contorno" onClick={handleVolver} disabled={isPending}>
              Volver
            </Boton>
            <Boton type="submit" variant="peligro" disabled={isPending || !motivo.trim()}>
              {isPending ? "Desistiendo…" : "Confirmar desistimiento"}
            </Boton>
          </footer>
        </form>
      ) : (
        <form onSubmit={handleReenviar} className="flex max-h-[90vh] flex-col">
          {encabezado("Corregir acta")}
          {avisoError}
          <div className="overflow-y-auto px-6 py-4">
            <fieldset disabled={isPending} className="flex min-w-0 flex-col gap-4">
              <DevolucionesActa acta={acta} />
              <DocumentosActa movimientoId={acta.id} />
              <div className="flex flex-col gap-2">
                <h3 className="text-sm font-semibold">Bienes · {bienes.length}</h3>
                {bienes.length > 0 ? (
                  <ListaBienesEntrega
                    bienes={bienes}
                    bloqueados={sinBloqueos}
                    conNovedad={conNovedad}
                    onQuitar={handleQuitar}
                  />
                ) : (
                  <p className="text-sm text-gray-600">El acta tiene que tener al menos un bien.</p>
                )}
              </div>
              {unidadOrigenId !== undefined && (
                <BuscadorBienes
                  unidadId={unidadOrigenId}
                  enLista={bienes}
                  propios={propios}
                  onSumar={(bien) => setBienes((actuales) => [...actuales, bien])}
                />
              )}
              <div className={claseCampo}>
                Unidad de destino
                <span className="font-normal">{acta.unidad_destino?.nombre}</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <label className={claseCampo}>
                  Número de acta
                  <input
                    required
                    pattern="[0-9]{4}/[0-9]{4}"
                    placeholder="0001/2026"
                    title="Cuatro dígitos y el año, por ejemplo 0001/2026"
                    value={datos.numeroActa}
                    onChange={cambiar("numeroActa")}
                    className={`${claseControl} font-mono`}
                  />
                  <span className="text-xs font-normal text-gray-500">Cuatro dígitos y el año</span>
                </label>
                <label className={claseCampo}>
                  Fecha del hecho
                  <input
                    type="date"
                    required
                    max={hoy()}
                    value={datos.fechaHecho}
                    onChange={cambiar("fechaHecho")}
                    className={`${claseControl} font-mono`}
                  />
                </label>
              </div>
              <label className={claseCampo}>
                Descripción
                <textarea
                  maxLength={500}
                  rows={3}
                  value={datos.descripcion}
                  onChange={cambiar("descripcion")}
                  className={claseControl}
                />
                <span className="text-xs font-normal text-gray-500">
                  Opcional, hasta 500 caracteres
                </span>
              </label>
            </fieldset>
          </div>
          <footer className="flex flex-wrap justify-between gap-2 border-t border-gray-200 px-6 py-3">
            <Boton type="button" variant="peligro" onClick={handleDesistir} disabled={isPending}>
              Desistir
            </Boton>
            <div className="flex gap-2">
              <Boton type="button" variant="contorno" onClick={onCerrar} disabled={isPending}>
                Cancelar
              </Boton>
              <Boton type="submit" disabled={isPending || bienes.length === 0}>
                {isPending ? "Reenviando…" : "Reenviar"}
              </Boton>
            </div>
          </footer>
        </form>
      )}
    </dialog>
  )
}
