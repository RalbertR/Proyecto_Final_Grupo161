import { useQuery } from "@tanstack/react-query"
import { useMemo } from "react"
import { useSearchParams } from "react-router-dom"
import { obtenerYo } from "../api/auth"
import { TablaInventario } from "../componentes/TablaInventario"
import { tiposDeBien } from "../tipos/bien"

export const InventarioPagina = () => {
  const { data: yo } = useQuery({ queryKey: ["yo"], queryFn: obtenerYo, retry: false })
  const verUnidades = !!yo && yo.unidad.nivel !== "OPERACIONAL"
  const [sp, setSp] = useSearchParams()
  const tipos = useMemo(() => sp.getAll("tipo"), [sp])

  const handleAlternarTipo = (codigo: string) =>
    setSp({ tipo: tipos.includes(codigo) ? tipos.filter((t) => t !== codigo) : [...tipos, codigo] })

  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 border-b border-gray-200 pb-4">
        <h1 className="text-2xl leading-tight font-semibold tracking-tight">Inventario</h1>
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
      <TablaInventario tipos={tipos} mostrarUnidad={verUnidades} />
    </section>
  )
}
