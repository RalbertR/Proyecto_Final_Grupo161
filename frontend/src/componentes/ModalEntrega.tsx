import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react"
import { registrarEntrega } from "../api/movimientos"
import { obtenerDestinos } from "../api/unidades"
import type { FilaInventario } from "../tipos/bien"
import { Boton } from "./Boton"
import { ListaBienesEntrega } from "./ListaBienesEntrega"
import { ResumenEntrega } from "./ResumenEntrega"

const hoy = () => {
  const ahora = new Date()
  const mes = String(ahora.getMonth() + 1).padStart(2, "0")
  const dia = String(ahora.getDate()).padStart(2, "0")
  return `${ahora.getFullYear()}-${mes}-${dia}`
}

const datosIniciales = () => ({ destino: "", numeroActa: "", fechaHecho: hoy(), descripcion: "" })

type Datos = ReturnType<typeof datosIniciales>

const claseCampo = "flex flex-col gap-2 text-sm font-semibold"
const claseControl =
  "min-h-11 rounded-xs border border-gray-300 bg-white px-3 py-2 font-normal hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco"

type ModalEntregaProps = {
  abierto: boolean
  unidadOrigen: string
  bienes: FilaInventario[]
  bloqueados: Map<number, string>
  onQuitar: (bienId: number) => void
  onCerrar: () => void
  onRegistrada: () => void
  onError: () => void
}

export const ModalEntrega = ({
  abierto,
  unidadOrigen,
  bienes,
  bloqueados,
  onQuitar,
  onCerrar,
  onRegistrada,
  onError,
}: ModalEntregaProps) => {
  const dialogo = useRef<HTMLDialogElement>(null)
  const enviando = useRef(false)
  const queryClient = useQueryClient()
  const [datos, setDatos] = useState(datosIniciales)
  const { data: destinos } = useQuery({
    queryKey: ["destinos"],
    queryFn: obtenerDestinos,
    enabled: abierto,
  })
  const {
    mutate,
    isPending,
    isError,
    error,
    data: registrada,
    reset,
  } = useMutation({
    mutationFn: registrarEntrega,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventario"] })
    },
    onError,
    onSettled: () => {
      enviando.current = false
    },
  })

  useEffect(() => {
    const d = dialogo.current
    if (abierto && !d?.open) d?.showModal()
    if (!abierto && d?.open) d.close()
  }, [abierto])

  const enviables = bienes.filter((b) => !bloqueados.has(b.bien_id))

  const cambiar =
    (campo: keyof Datos) =>
    (e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setDatos((actual) => ({ ...actual, [campo]: e.target.value }))

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (enviando.current) return
    enviando.current = true
    mutate({
      unidad_destino_id: Number(datos.destino),
      numero_acta: datos.numeroActa,
      fecha_hecho: datos.fechaHecho,
      descripcion: datos.descripcion.trim() || null,
      bienes: enviables.map((b) => b.bien_id),
    })
  }

  const empezarDeNuevo = () => {
    setDatos(datosIniciales())
    reset()
  }

  const handleCerrar = () => {
    if (!isPending) reset()
    onCerrar()
  }

  const handleCancelar = () => {
    empezarDeNuevo()
    onCerrar()
  }

  const handleVolver = () => {
    empezarDeNuevo()
    onRegistrada()
  }

  return (
    <dialog
      ref={dialogo}
      onClose={registrada ? handleVolver : handleCerrar}
      aria-labelledby="titulo-entrega"
      className="m-auto w-full max-w-lg rounded-xs p-0 text-gray-900 shadow-xl backdrop:bg-gray-900/45"
    >
      {registrada ? (
        <div className="flex max-h-[90vh] flex-col">
          <header className="border-b border-gray-200 px-6 py-4">
            <h2 id="titulo-entrega" className="text-lg font-semibold">
              Entrega registrada
            </h2>
          </header>
          <div className="overflow-y-auto px-6 py-4">
            <ResumenEntrega movimiento={registrada} />
          </div>
          <footer className="flex justify-end border-t border-gray-200 px-6 py-3">
            <Boton onClick={handleVolver}>Volver al inventario</Boton>
          </footer>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex max-h-[90vh] flex-col">
          <header className="flex items-baseline justify-between gap-4 border-b border-gray-200 px-6 py-4">
            <h2 id="titulo-entrega" className="text-lg font-semibold">
              Nueva entrega
            </h2>
            <span className="text-sm text-gray-500">Desde {unidadOrigen}</span>
          </header>
          <div className="flex flex-col gap-4 overflow-y-auto px-6 py-4">
            {isError && (
              <div
                role="alert"
                className="rounded-xs border border-error bg-error/5 px-4 py-3 text-sm font-medium text-error"
              >
                {error.message}
              </div>
            )}
            <div className="flex flex-col gap-2">
              <div className="flex items-baseline justify-between gap-4">
                <h3 className="text-sm font-semibold">Bienes · {enviables.length}</h3>
                <button
                  type="button"
                  onClick={handleCerrar}
                  className="text-sm font-semibold text-marca underline hover:text-marca-hover focus-visible:outline-3 focus-visible:outline-foco"
                >
                  + Sumar bienes
                </button>
              </div>
              <ListaBienesEntrega bienes={bienes} bloqueados={bloqueados} onQuitar={onQuitar} />
            </div>
            <label className={claseCampo}>
              Unidad de destino
              <select
                required
                value={datos.destino}
                onChange={cambiar("destino")}
                className={claseControl}
              >
                <option value="">Elegí una unidad</option>
                {destinos?.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.nombre}
                  </option>
                ))}
              </select>
            </label>
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
          </div>
          <footer className="flex justify-end gap-2 border-t border-gray-200 px-6 py-3">
            <Boton type="button" variant="contorno" onClick={handleCancelar}>
              Cancelar
            </Boton>
            <Boton type="submit" disabled={isPending || enviables.length === 0}>
              {isPending ? "Registrando…" : "Registrar entrega"}
            </Boton>
          </footer>
        </form>
      )}
    </dialog>
  )
}
