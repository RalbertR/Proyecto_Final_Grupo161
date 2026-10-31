import { useQuery } from "@tanstack/react-query"
import { useCallback, useMemo, useState, type ChangeEvent } from "react"
import { useSearchParams } from "react-router-dom"
import { obtenerYo } from "../api/auth"
import { obtenerUnidades } from "../api/unidades"
import { BarraSeleccion } from "../componentes/BarraSeleccion"
import { ModalEntrega } from "../componentes/ModalEntrega"
import { TablaInventario } from "../componentes/TablaInventario"
import { areasDe, tiposDeBien, type FilaInventario } from "../tipos/bien"

const sinBloqueados = new Map<number, string>()

export const InventarioPagina = () => {
  const { data: yo } = useQuery({ queryKey: ["yo"], queryFn: obtenerYo, retry: false })
  const verUnidades = !!yo && yo.unidad.nivel !== "OPERACIONAL"
  const { data: unidades } = useQuery({
    queryKey: ["unidades"],
    queryFn: obtenerUnidades,
    enabled: verUnidades,
  })
  const [sp, setSp] = useSearchParams()
  const tipos = useMemo(() => sp.getAll("tipo"), [sp])
  const unidad = sp.get("unidad") ?? ""

  const filtrar = (nuevosTipos: string[], nuevaUnidad: string) =>
    setSp(nuevaUnidad ? { unidad: nuevaUnidad, tipo: nuevosTipos } : { tipo: nuevosTipos })

  const handleAlternarTipo = (codigo: string) =>
    filtrar(tipos.includes(codigo) ? tipos.filter((t) => t !== codigo) : [...tipos, codigo], unidad)

  const handleElegirUnidad = (e: ChangeEvent<HTMLSelectElement>) => filtrar(tipos, e.target.value)

  const [seleccion, setSeleccion] = useState<FilaInventario[]>([])
  const [avisoArea, setAvisoArea] = useState(false)
  const [modalAbierto, setModalAbierto] = useState(false)

  const handleAlternar = useCallback((bien: FilaInventario) => {
    setSeleccion((actual) =>
      actual.some((b) => b.bien_id === bien.bien_id)
        ? actual.filter((b) => b.bien_id !== bien.bien_id)
        : [...actual, bien],
    )
    setAvisoArea(false)
  }, [])

  const handleLimpiar = () => {
    setSeleccion([])
    setAvisoArea(false)
  }

  const handleNuevaEntrega = () => {
    if (areasDe(seleccion).length > 1) setAvisoArea(true)
    else setModalAbierto(true)
  }

  const handleQuitar = (bienId: number) =>
    setSeleccion((actual) => actual.filter((b) => b.bien_id !== bienId))

  const handleCerrarModal = () => setModalAbierto(false)

  const handleRegistrada = () => {
    setModalAbierto(false)
    setSeleccion([])
  }

  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 border-b border-gray-200 pb-4">
        <h1 className="text-2xl leading-tight font-semibold tracking-tight">Inventario</h1>
        {verUnidades && (
          <label className="flex max-w-sm flex-col gap-2 text-sm font-semibold">
            Unidad
            <select
              value={unidad}
              onChange={handleElegirUnidad}
              className="min-h-11 rounded-xs border border-gray-300 bg-white px-3 py-2 font-normal hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco"
            >
              <option value="">Todas las unidades</option>
              {unidades?.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.nombre}
                </option>
              ))}
            </select>
          </label>
        )}
        <fieldset>
          <legend className="mb-2 text-sm font-semibold">Tipo de bien</legend>
          <div className="flex flex-wrap gap-2">
            {Object.entries(tiposDeBien).map(([codigo, nombre]) => {
              const marcado = tipos.includes(codigo)
              return (
                <label
                  key={codigo}
                  className={`inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-xs border px-3 py-2 text-sm font-semibold transition ${marcado ? "border-marca bg-marca/5" : "border-gray-300 text-gray-600 hover:border-gray-500"}`}
                >
                  <input
                    type="checkbox"
                    checked={marcado}
                    onChange={() => handleAlternarTipo(codigo)}
                    className="size-4 accent-marca focus-visible:outline-3 focus-visible:outline-foco"
                  />
                  {nombre}
                </label>
              )
            })}
          </div>
        </fieldset>
      </div>
      <TablaInventario
        tipos={tipos}
        mostrarUnidad={verUnidades}
        unidadId={Number(unidad) || undefined}
        unidadPropiaId={yo?.unidad.id}
        seleccion={seleccion}
        onAlternar={handleAlternar}
      />
      <BarraSeleccion
        seleccion={seleccion}
        avisoArea={avisoArea}
        onLimpiar={handleLimpiar}
        onNuevaEntrega={handleNuevaEntrega}
      />
      {yo && (
        <ModalEntrega
          abierto={modalAbierto}
          unidadOrigen={yo.unidad.nombre}
          bienes={seleccion}
          bloqueados={sinBloqueados}
          onQuitar={handleQuitar}
          onCerrar={handleCerrarModal}
          onRegistrada={handleRegistrada}
          onError={() => {}}
        />
      )}
    </section>
  )
}
