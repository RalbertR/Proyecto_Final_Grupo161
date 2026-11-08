import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react"
import { obtenerInventario } from "../api/inventario"
import { registrarDotacion } from "../api/movimientos"
import { obtenerOficiales } from "../api/oficiales"
import {
  coincideOficial,
  oficialesQueCumplen,
  textoTipos,
  type FilaInventario,
} from "../tipos/bien"
import { hoy, type Oficial } from "../tipos/movimiento"
import { Boton } from "./Boton"
import { ListaBienesEntrega } from "./ListaBienesEntrega"
import { ResumenDotacion } from "./ResumenDotacion"

const datosIniciales = () => ({ numeroActa: "", fechaHecho: "", descripcion: "" })

type Datos = ReturnType<typeof datosIniciales>

const claseCampo = "flex flex-col gap-2 text-sm font-semibold"
const claseControl =
  "min-h-11 rounded-xs border border-gray-300 bg-white px-3 py-2 font-normal hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco"
const claseEnlace =
  "text-sm font-semibold text-marca underline hover:text-marca-hover focus-visible:outline-3 focus-visible:outline-foco disabled:cursor-not-allowed disabled:opacity-50"
const sinOficiales: Oficial[] = []
const sinInventario: FilaInventario[] = []

type ModalDotacionProps = {
  abierto: boolean
  unidadId: number
  unidadOrigen: string
  bienes: FilaInventario[]
  bloqueados: Map<number, string>
  onQuitar: (bienId: number) => void
  onCerrar: () => void
  onRegistrada: () => void
  onError: () => void
}

export const ModalDotacion = ({
  abierto,
  unidadId,
  unidadOrigen,
  bienes,
  bloqueados,
  onQuitar,
  onCerrar,
  onRegistrada,
  onError,
}: ModalDotacionProps) => {
  const dialogo = useRef<HTMLDialogElement>(null)
  const enviando = useRef(false)
  const queryClient = useQueryClient()
  const [datos, setDatos] = useState(datosIniciales)
  const [elegido, setElegido] = useState<Oficial | null>(null)
  const [texto, setTexto] = useState("")
  const { data: oficiales = sinOficiales, isError: sinListaDeOficiales } = useQuery({
    queryKey: ["oficiales"],
    queryFn: obtenerOficiales,
    enabled: abierto,
    retry: false,
  })
  const { data: inventario = sinInventario } = useQuery({
    queryKey: ["inventario", unidadId],
    queryFn: () => obtenerInventario(unidadId),
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
    mutationFn: registrarDotacion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventario"] })
      queryClient.invalidateQueries({ queryKey: ["oficiales"] })
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

  const enviables = bienes.filter((b) => !bloqueados.has(b.bien_id))
  const tipos = [...new Set(enviables.map((b) => b.tipo_bien))]
  const cumplen = oficialesQueCumplen(oficiales, inventario, tipos)
  const oficial = cumplen.find((o) => o.id === elegido?.id) ?? null
  const coincidencias = texto.trim()
    ? cumplen.filter((o) => coincideOficial(o, texto)).slice(0, 8)
    : sinOficiales

  const cambiar =
    (campo: keyof Datos) => (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setDatos((actual) => ({ ...actual, [campo]: e.target.value }))

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (enviando.current || !oficial) return
    enviando.current = true
    mutate({
      oficial_id: oficial.id,
      numero_acta: datos.numeroActa,
      fecha_hecho: datos.fechaHecho || hoy(),
      descripcion: datos.descripcion.trim() || null,
      bienes: enviables.map((b) => b.bien_id),
    })
  }

  const empezarDeNuevo = () => {
    setDatos(datosIniciales())
    setElegido(null)
    setTexto("")
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
      aria-labelledby="titulo-dotacion"
      className="m-auto w-full max-w-lg rounded-xs p-0 text-gray-900 shadow-xl backdrop:bg-gray-900/45"
    >
      {registrada ? (
        <div className="flex max-h-[90vh] flex-col">
          <header className="border-b border-gray-200 px-6 py-4">
            <h2 id="titulo-dotacion" className="text-lg font-semibold">
              Dotación registrada
            </h2>
          </header>
          <div className="overflow-y-auto px-6 py-4">
            <ResumenDotacion movimiento={registrada} />
          </div>
          <footer className="flex justify-end border-t border-gray-200 px-6 py-3">
            <Boton onClick={handleVolver}>Volver al inventario</Boton>
          </footer>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex max-h-[90vh] flex-col">
          <header className="flex items-baseline justify-between gap-4 border-b border-gray-200 px-6 py-4">
            <h2 id="titulo-dotacion" className="text-lg font-semibold">
              Asignar a oficial
            </h2>
            <span className="text-sm text-gray-500">Desde {unidadOrigen}</span>
          </header>
          {isError && (
            <div
              role="alert"
              className="mx-6 mt-4 shrink-0 rounded-xs border border-error bg-error/5 px-4 py-3 text-sm font-medium text-error"
            >
              {error.message}
            </div>
          )}
          {sinListaDeOficiales && (
            <div
              role="alert"
              className="mx-6 mt-4 shrink-0 rounded-xs border border-error bg-error/5 px-4 py-3 text-sm font-medium text-error"
            >
              No se pudieron cargar los oficiales
            </div>
          )}
          <div className="overflow-y-auto px-6 py-4">
            <fieldset disabled={isPending} className="flex min-w-0 flex-col gap-4">
              <div className="flex flex-col gap-2">
                <div className="flex items-baseline justify-between gap-4">
                  <h3 className="text-sm font-semibold">Bienes · {enviables.length}</h3>
                  <button type="button" onClick={handleCerrar} className={claseEnlace}>
                    + Sumar bienes
                  </button>
                </div>
                <ListaBienesEntrega bienes={bienes} bloqueados={bloqueados} onQuitar={onQuitar} />
              </div>
              {oficial ? (
                <div className={claseCampo}>
                  Oficial
                  <div className="flex items-center justify-between gap-3 rounded-xs border border-marca bg-gray-50 px-3 py-2 font-normal">
                    <span>
                      <span className="font-mono">{oficial.legajo}</span> · {oficial.nombre}
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setElegido(null)
                        setTexto("")
                      }}
                      className={claseEnlace}
                    >
                      Cambiar
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  <label className={claseCampo}>
                    Oficial
                    <input
                      value={texto}
                      onChange={(e) => setTexto(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") e.preventDefault()
                      }}
                      className={claseControl}
                    />
                    <span className="text-xs font-normal text-gray-500">
                      Legajo o apellido. Solo aparecen los que no tienen {textoTipos(tipos)}{" "}
                      asignado.
                    </span>
                  </label>
                  {texto.trim() &&
                    (coincidencias.length ? (
                      <ul className="divide-y divide-gray-100 rounded-xs border border-gray-200">
                        {coincidencias.map((o) => (
                          <li
                            key={o.id}
                            className="flex items-center justify-between gap-3 px-3 py-1.5 text-sm"
                          >
                            <span>
                              <span className="font-mono">{o.legajo}</span> · {o.nombre}
                            </span>
                            <button
                              type="button"
                              onClick={() => setElegido(o)}
                              aria-label={`Elegir ${o.nombre}`}
                              className={claseEnlace}
                            >
                              Elegir
                            </button>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-gray-500">
                        Ningún oficial activo sin {textoTipos(tipos)} asignado
                      </p>
                    ))}
                </div>
              )}
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
            <Boton type="submit" disabled={isPending || !oficial || enviables.length === 0}>
              {isPending ? "Asignando…" : "Asignar"}
            </Boton>
          </footer>
        </form>
      )}
    </dialog>
  )
}
