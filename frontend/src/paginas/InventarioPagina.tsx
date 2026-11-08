import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useMemo, useState, type ChangeEvent } from "react"
import { useSearchParams } from "react-router-dom"
import { obtenerYo } from "../api/auth"
import { obtenerInventario } from "../api/inventario"
import { obtenerUnidades } from "../api/unidades"
import { BarraSeleccion, type AvisoBarra } from "../componentes/BarraSeleccion"
import { ModalDevolucion } from "../componentes/ModalDevolucion"
import { ModalDotacion } from "../componentes/ModalDotacion"
import { ModalEntrega } from "../componentes/ModalEntrega"
import { TablaInventario } from "../componentes/TablaInventario"
import {
  areasDe,
  motivoBloqueo,
  motivoParaDevolver,
  oficialesDe,
  tiposDeBien,
  tiposRepetidos,
  type FilaInventario,
} from "../tipos/bien"

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
  const [aviso, setAviso] = useState<AvisoBarra | null>(null)
  const [modalAbierto, setModalAbierto] = useState(false)
  const [devolucionAbierta, setDevolucionAbierta] = useState(false)
  const [dotacionAbierta, setDotacionAbierta] = useState(false)
  const [bloqueados, setBloqueados] = useState(sinBloqueados)
  const queryClient = useQueryClient()

  const handleAlternar = useCallback((bien: FilaInventario) => {
    setSeleccion((actual) =>
      actual.some((b) => b.bien_id === bien.bien_id)
        ? actual.filter((b) => b.bien_id !== bien.bien_id)
        : [...actual, bien],
    )
    setAviso(null)
  }, [])

  const handleLimpiar = () => {
    setSeleccion([])
    setAviso(null)
  }

  const handleNuevaEntrega = () => {
    if (areasDe(seleccion).length > 1) setAviso("areas")
    else setModalAbierto(true)
  }

  const handleAsignarAOficial = () => {
    if (seleccion.some((b) => b.estado_operativo === "FUERA_DE_SERVICIO"))
      setAviso("fueraDeServicio")
    else if (tiposRepetidos(seleccion)) setAviso("mismoTipo")
    else if (areasDe(seleccion).length > 1) setAviso("areas")
    else setDotacionAbierta(true)
  }

  const handleRegistrarDevolucion = () => {
    if (oficialesDe(seleccion).length > 1) setAviso("oficiales")
    else if (areasDe(seleccion).length > 1) setAviso("areas")
    else setDevolucionAbierta(true)
  }

  const handleQuitar = (bienId: number) =>
    setSeleccion((actual) => actual.filter((b) => b.bien_id !== bienId))

  const handleCerrarModal = () => {
    setModalAbierto(false)
    setDevolucionAbierta(false)
    setDotacionAbierta(false)
    setSeleccion((actual) => actual.filter((b) => !bloqueados.has(b.bien_id)))
    setBloqueados(sinBloqueados)
  }

  const handleRegistrada = () => {
    setModalAbierto(false)
    setDevolucionAbierta(false)
    setDotacionAbierta(false)
    setSeleccion([])
    setBloqueados(sinBloqueados)
  }

  const marcarBloqueados = async (regla: (fresca: FilaInventario | undefined) => string | null) => {
    if (!yo) return
    queryClient.invalidateQueries({ queryKey: ["inventario"] })
    const frescas = await queryClient
      .fetchQuery({
        queryKey: ["inventario", yo.unidad.id],
        queryFn: () => obtenerInventario(yo.unidad.id),
      })
      .catch(() => null)
    if (!frescas) return
    const motivos = new Map<number, string>()
    for (const bien of seleccion) {
      const motivo = regla(frescas.find((f) => f.bien_id === bien.bien_id))
      if (motivo) motivos.set(bien.bien_id, motivo)
    }
    setBloqueados(motivos)
  }

  const handleErrorEntrega = () =>
    marcarBloqueados((fresca) =>
      fresca ? motivoBloqueo(fresca, yo?.unidad.id) : "Ya no está en el inventario",
    )

  const handleErrorDevolucion = () => {
    const oficialId = seleccion[0]?.oficial_id
    if (oficialId == null) return
    marcarBloqueados((fresca) => motivoParaDevolver(fresca, oficialId))
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
        aviso={aviso}
        onLimpiar={handleLimpiar}
        onNuevaEntrega={handleNuevaEntrega}
        onAsignarAOficial={handleAsignarAOficial}
        onRegistrarDevolucion={handleRegistrarDevolucion}
      />
      {yo && (
        <ModalEntrega
          abierto={modalAbierto}
          unidadOrigen={yo.unidad.nombre}
          bienes={seleccion}
          bloqueados={bloqueados}
          onQuitar={handleQuitar}
          onCerrar={handleCerrarModal}
          onRegistrada={handleRegistrada}
          onError={handleErrorEntrega}
        />
      )}
      {yo && (
        <ModalDotacion
          abierto={dotacionAbierta}
          unidadId={yo.unidad.id}
          unidadOrigen={yo.unidad.nombre}
          bienes={seleccion}
          bloqueados={bloqueados}
          onQuitar={handleQuitar}
          onCerrar={handleCerrarModal}
          onRegistrada={handleRegistrada}
          onError={handleErrorEntrega}
        />
      )}
      <ModalDevolucion
        abierto={devolucionAbierta}
        bienes={seleccion}
        bloqueados={bloqueados}
        onQuitar={handleQuitar}
        onCerrar={handleCerrarModal}
        onRegistrada={handleRegistrada}
        onError={handleErrorDevolucion}
      />
    </section>
  )
}
