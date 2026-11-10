import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react"
import { registrarDevolucion } from "../api/movimientos"
import { obtenerUbicaciones } from "../api/unidades"
import { nombreEstadoOperativo, tiposDeBien, type FilaInventario } from "../tipos/bien"
import { hoy, ubicacionPorDefecto } from "../tipos/movimiento"
import { Boton } from "./Boton"
import { Marca } from "./Marca"
import { ResumenDevolucion } from "./ResumenDevolucion"

const datosIniciales = () => ({ numeroActa: "", fechaHecho: "", descripcion: "" })

type Datos = ReturnType<typeof datosIniciales>

const claseCampo = "flex flex-col gap-2 text-sm font-semibold"
const claseControl =
  "min-h-11 rounded-xs border border-gray-300 bg-white px-3 py-2 font-normal hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco"

type ModalDevolucionProps = {
  abierto: boolean
  bienes: FilaInventario[]
  bloqueados: Map<number, string>
  onQuitar: (bienId: number) => void
  onCerrar: () => void
  onRegistrada: () => void
  onError: () => void
}

export const ModalDevolucion = ({
  abierto,
  bienes,
  bloqueados,
  onQuitar,
  onCerrar,
  onRegistrada,
  onError,
}: ModalDevolucionProps) => {
  const dialogo = useRef<HTMLDialogElement>(null)
  const enviando = useRef(false)
  const queryClient = useQueryClient()
  const [datos, setDatos] = useState(datosIniciales)
  const [elegidas, setElegidas] = useState<Record<number, number>>({})
  const { data: ubicaciones, isError: sinUbicaciones } = useQuery({
    queryKey: ["ubicaciones"],
    queryFn: obtenerUbicaciones,
    enabled: abierto,
    retry: false,
  })
  const {
    mutate,
    isPending,
    isError,
    error,
    data: registrada,
    reset,
  } = useMutation({
    mutationFn: registrarDevolucion,
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

  useEffect(() => {
    const frenarEscape = (e: KeyboardEvent) => {
      if (enviando.current && e.key === "Escape") e.preventDefault()
    }
    document.addEventListener("keydown", frenarEscape, true)
    return () => document.removeEventListener("keydown", frenarEscape, true)
  }, [])

  const oficial = bienes[0]
  const enviables = bienes.filter((b) => !bloqueados.has(b.bien_id))
  const ubicacionDe = (bien: FilaInventario) =>
    elegidas[bien.bien_id] ?? ubicacionPorDefecto(bien.tipo_bien, ubicaciones ?? [])
  const faltaUbicacion = enviables.some((b) => ubicacionDe(b) === undefined)
  const comunes = new Set(enviables.map(ubicacionDe))
  const todas = comunes.size === 1 ? String([...comunes][0] ?? "") : ""

  const cambiar =
    (campo: keyof Datos) => (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setDatos((actual) => ({ ...actual, [campo]: e.target.value }))

  const elegir = (bienId: number, valor: string) =>
    setElegidas((actual) => {
      const nuevas = { ...actual }
      if (valor) nuevas[bienId] = Number(valor)
      else delete nuevas[bienId]
      return nuevas
    })

  const elegirTodas = (valor: string) => {
    if (!valor) return
    setElegidas((actual) => ({
      ...actual,
      ...Object.fromEntries(bienes.map((b) => [b.bien_id, Number(valor)])),
    }))
  }

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (enviando.current || oficial?.oficial_id == null) return
    const ubicacionesElegidas = enviables.flatMap((b) => {
      const ubicacionId = ubicacionDe(b)
      return ubicacionId === undefined ? [] : [{ bien_id: b.bien_id, ubicacion_id: ubicacionId }]
    })
    if (ubicacionesElegidas.length !== enviables.length) return
    enviando.current = true
    mutate({
      oficial_id: oficial.oficial_id,
      numero_acta: datos.numeroActa,
      fecha_hecho: datos.fechaHecho || hoy(),
      descripcion: datos.descripcion.trim() || null,
      ubicaciones: ubicacionesElegidas,
    })
  }

  const empezarDeNuevo = () => {
    setDatos(datosIniciales())
    setElegidas({})
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
      onCancel={(e) => {
        if (isPending) e.preventDefault()
      }}
      onClose={registrada ? handleVolver : handleCerrar}
      aria-labelledby="titulo-devolucion"
      className="m-auto w-full max-w-4xl rounded-xs p-0 text-gray-900 shadow-xl backdrop:bg-gray-900/45"
    >
      {registrada ? (
        <div className="flex max-h-[90vh] flex-col">
          <header className="border-b border-gray-200 px-6 py-4">
            <h2 id="titulo-devolucion" className="text-lg font-semibold">
              Devolución registrada
            </h2>
          </header>
          <div className="overflow-y-auto px-6 py-4">
            <ResumenDevolucion movimiento={registrada} />
          </div>
          <footer className="flex justify-end border-t border-gray-200 px-6 py-3">
            <Boton onClick={handleVolver}>Volver al inventario</Boton>
          </footer>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex max-h-[90vh] flex-col">
          <header className="flex items-baseline justify-between gap-4 border-b border-gray-200 px-6 py-4">
            <h2 id="titulo-devolucion" className="text-lg font-semibold">
              Registrar devolución
            </h2>
            {oficial && (
              <span className="text-sm text-gray-500">
                De <span className="font-mono">{oficial.oficial_legajo}</span> · {oficial.oficial}
              </span>
            )}
          </header>
          {isError && (
            <div
              role="alert"
              className="mx-6 mt-4 shrink-0 rounded-xs border border-error bg-error/5 px-4 py-3 text-sm font-medium text-error"
            >
              {error.message}
            </div>
          )}
          {sinUbicaciones && (
            <div
              role="alert"
              className="mx-6 mt-4 shrink-0 rounded-xs border border-error bg-error/5 px-4 py-3 text-sm font-medium text-error"
            >
              No se pudieron cargar las ubicaciones
            </div>
          )}
          <div className="overflow-y-auto px-6 py-4">
            <fieldset disabled={isPending} className="flex min-w-0 flex-col gap-4">
              <div className="flex flex-col gap-2">
                <div className="flex items-baseline justify-between gap-4">
                  <h3 className="text-sm font-semibold">Bienes · {enviables.length}</h3>
                  <button
                    type="button"
                    onClick={handleCerrar}
                    className="text-sm font-semibold text-marca underline hover:text-marca-hover focus-visible:outline-3 focus-visible:outline-foco disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    + Sumar bienes
                  </button>
                </div>
                <label className="flex flex-wrap items-center gap-3 rounded-xs border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-semibold">
                  La misma ubicación para todos
                  <select
                    value={todas}
                    onChange={(e) => elegirTodas(e.target.value)}
                    className={claseControl}
                  >
                    <option value="">Elegí una ubicación</option>
                    {ubicaciones?.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.nombre}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="overflow-x-auto">
                  <table className="w-full bg-white text-left text-sm">
                    <thead className="border-b border-gray-500">
                      <tr>
                        {["Tipo", "Marca", "Modelo", "Identificación", "Estado", "Ubicación"].map(
                          (columna) => (
                            <th
                              key={columna}
                              scope="col"
                              className="px-3 py-2 font-semibold whitespace-nowrap"
                            >
                              {columna}
                            </th>
                          ),
                        )}
                        <th scope="col" className="px-3 py-2">
                          <span className="sr-only">Quitar</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {bienes.map((bien) => {
                        const motivo = bloqueados.get(bien.bien_id)
                        return (
                          <tr key={bien.bien_id} className="border-b border-gray-200">
                            <td
                              className={`px-3 py-1 ${motivo ? "text-gray-400 line-through" : ""}`}
                            >
                              {tiposDeBien[bien.tipo_bien] ?? bien.tipo_bien}
                            </td>
                            <td className="px-3 py-1">{bien.marca}</td>
                            <td className="px-3 py-1">{bien.modelo}</td>
                            <td className="px-3 py-1 font-mono">{bien.identificacion}</td>
                            <td className="px-3 py-1 whitespace-nowrap">
                              {nombreEstadoOperativo[bien.estado_operativo]}
                            </td>
                            <td className="px-3 py-1">
                              {motivo ? (
                                <Marca>{motivo}</Marca>
                              ) : (
                                <select
                                  value={ubicacionDe(bien) ?? ""}
                                  onChange={(e) => elegir(bien.bien_id, e.target.value)}
                                  aria-label={`Ubicación ${bien.identificacion}`}
                                  className={claseControl}
                                >
                                  <option value="">Elegí una ubicación</option>
                                  {ubicaciones?.map((u) => (
                                    <option key={u.id} value={u.id}>
                                      {u.nombre}
                                    </option>
                                  ))}
                                </select>
                              )}
                            </td>
                            <td className="px-3 py-1 text-right">
                              <button
                                type="button"
                                onClick={() => onQuitar(bien.bien_id)}
                                aria-label={`Quitar ${bien.identificacion}`}
                                className="inline-flex size-8 shrink-0 items-center justify-center rounded-xs text-lg leading-none text-gray-500 hover:bg-gray-100 hover:text-gray-900 focus-visible:outline-3 focus-visible:outline-foco disabled:cursor-not-allowed disabled:opacity-50"
                              >
                                ×
                              </button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
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
                    value={datos.fechaHecho || hoy()}
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
                  placeholder="Por ejemplo, devolución por retiro"
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
          <footer className="flex justify-end gap-2 border-t border-gray-200 px-6 py-3">
            <Boton type="button" variant="contorno" onClick={handleCancelar} disabled={isPending}>
              Cancelar
            </Boton>
            <Boton
              type="submit"
              disabled={isPending || !ubicaciones || enviables.length === 0 || faltaUbicacion}
            >
              {isPending ? "Registrando…" : "Registrar devolución"}
            </Boton>
          </footer>
        </form>
      )}
    </dialog>
  )
}
