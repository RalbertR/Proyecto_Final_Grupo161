import { useQuery } from "@tanstack/react-query"
import { useState, type ChangeEvent } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { obtenerYo } from "../api/auth"
import { obtenerSituacion } from "../api/situacion"
import { obtenerUnidades } from "../api/unidades"
import { ModalActa } from "../componentes/ModalActa"
import { TablaSituacion, type Celda } from "../componentes/TablaSituacion"
import { tiposDeBien } from "../tipos/bien"
import { fechaDeHoyEnLetras } from "../tipos/pendiente"
import {
  antiguedad,
  etapaDelActa,
  fraseSituacion,
  nombreEtapa,
  textoDias,
} from "../tipos/situacion"

const claseEtiqueta = "font-etiqueta text-xs font-semibold tracking-wider text-gray-500 uppercase"

export const SituacionPagina = () => {
  const { data: yo } = useQuery({ queryKey: ["yo"], queryFn: obtenerYo, retry: false })
  const direccion = yo?.unidad.nivel === "DIRECCION"
  const [sp, setSp] = useSearchParams()
  const regionalId = Number(sp.get("regional")) || undefined
  const { data: unidades } = useQuery({
    queryKey: ["unidades"],
    queryFn: obtenerUnidades,
    enabled: direccion,
  })
  const { data, isPending, isError, error } = useQuery({
    queryKey: ["situacion", regionalId ?? null],
    queryFn: () => obtenerSituacion(regionalId),
    enabled: !!yo,
    retry: false,
  })
  const [celda, setCelda] = useState<Celda | null>(null)
  const [actaId, setActaId] = useState<number | null>(null)

  const handleMostrar = (e: ChangeEvent<HTMLSelectElement>) => {
    setCelda(null)
    setSp(e.target.value ? { regional: e.target.value } : {})
  }

  return (
    <section className="flex flex-col gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <p className="font-etiqueta text-sm font-semibold tracking-wider text-gray-500 uppercase">
            {fechaDeHoyEnLetras(new Date())}
          </p>
          <h1 className="text-2xl leading-tight font-semibold tracking-tight">
            {data ? fraseSituacion(data.grupos) : "Sala de situación"}
          </h1>
        </div>
        {direccion && (
          <label className="flex flex-col gap-1 text-sm font-semibold">
            Mostrar
            <select
              value={regionalId ?? ""}
              onChange={handleMostrar}
              className="min-h-11 rounded-xs border border-gray-300 bg-white px-3 py-2 font-normal hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco"
            >
              <option value="">Toda la jurisdicción</option>
              {unidades
                ?.filter((u) => u.nivel === "REGIONAL")
                .map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.nombre}
                  </option>
                ))}
            </select>
          </label>
        )}
      </header>

      {isError && (
        <p
          role="alert"
          className="rounded-xs border border-error bg-white px-4 py-3 text-sm font-medium text-error"
        >
          {error.message}
        </p>
      )}

      {isPending && !isError && (
        <div aria-busy="true" className="space-y-3">
          <div className="h-24 animate-pulse rounded-xs bg-gray-200" />
          <div className="h-72 animate-pulse rounded-xs bg-gray-200" />
        </div>
      )}

      {data && (
        <>
          <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {data.grupos.map((g) => (
              <li
                key={g.etapa}
                className="flex items-end justify-between gap-3 rounded-xs border border-gray-300 bg-white px-4 py-3"
              >
                <div className="flex flex-col gap-1">
                  <span className={claseEtiqueta}>{nombreEtapa[g.etapa]}</span>
                  <span className="text-sm text-gray-600">{antiguedad(g)}</span>
                </div>
                <span className="font-mono text-3xl font-medium">{g.cantidad}</span>
              </li>
            ))}
          </ul>

          <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
            <div className="flex min-w-0 flex-col gap-3">
              <TablaSituacion unidades={data.unidades} elegida={celda} onElegir={setCelda} />
              {celda && (
                <p className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-xs border border-gray-300 bg-white px-4 py-3 text-sm">
                  <span>
                    {celda.unidad.nombre},{" "}
                    {tiposDeBien[celda.tipo.tipo_bien] ?? celda.tipo.tipo_bien}: {celda.tipo.total}{" "}
                    {celda.tipo.total === 1 ? "bien" : "bienes"}, {celda.tipo.fuera_de_servicio}{" "}
                    fuera de servicio
                  </span>
                  <Link
                    to={`/inventario?unidad=${celda.unidad.id}&tipo=${celda.tipo.tipo_bien}`}
                    className="font-semibold text-marca underline hover:text-marca-hover focus-visible:outline-3 focus-visible:outline-foco"
                  >
                    Ver en el inventario
                  </Link>
                </p>
              )}
            </div>

            <section
              aria-labelledby="titulo-demoradas"
              className="rounded-xs border border-gray-300 bg-white"
            >
              <h2
                id="titulo-demoradas"
                className="border-b border-gray-200 px-4 py-3 text-lg font-semibold"
              >
                Más demoradas
              </h2>
              {data.demoradas.length === 0 ? (
                <p className="px-4 py-6 text-sm text-gray-600">No hay actas abiertas.</p>
              ) : (
                <ol className="divide-y divide-gray-200">
                  {data.demoradas.map((d) => (
                    <li
                      key={d.movimiento_id}
                      className="flex items-center justify-between gap-3 px-4 py-3"
                    >
                      <div className="flex min-w-0 flex-col gap-0.5">
                        <button
                          type="button"
                          onClick={() => setActaId(d.movimiento_id)}
                          className="w-fit font-mono font-medium underline hover:text-gray-600 focus-visible:outline-2 focus-visible:outline-foco"
                        >
                          {d.numero_acta ?? "Sin acta"}
                        </button>
                        <span className="text-sm text-gray-600">
                          {etapaDelActa[d.etapa]} · {d.unidad}
                        </span>
                      </div>
                      <span className="shrink-0 font-mono text-sm font-semibold">
                        {d.dias === 0 ? "Menos de un día" : textoDias(d.dias)}
                      </span>
                    </li>
                  ))}
                </ol>
              )}
            </section>
          </div>
        </>
      )}

      {actaId !== null && <ModalActa movimientoId={actaId} onCerrar={() => setActaId(null)} />}
    </section>
  )
}
