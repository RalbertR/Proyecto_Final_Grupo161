import {
  intensidad,
  nombreTipoCorto,
  type TipoSituacion,
  type UnidadSituacion,
} from "../tipos/situacion"

export type Celda = { unidad: UnidadSituacion; tipo: TipoSituacion }

const fondo = (nivel: number) => `rgb(163 22 33 / ${(0.06 + 0.6 * nivel).toFixed(2)})`

const claseCabecera =
  "px-3 py-2 font-etiqueta text-xs font-semibold tracking-wider text-gray-500 uppercase"

type TablaSituacionProps = {
  unidades: UnidadSituacion[]
  elegida: Celda | null
  onElegir: (celda: Celda) => void
}

export const TablaSituacion = ({ unidades, elegida, onElegir }: TablaSituacionProps) => {
  const tipos = unidades[0]?.tipos.map((t) => t.tipo_bien) ?? []
  const totalDe = (u: UnidadSituacion) => u.tipos.reduce((suma, t) => suma + t.total, 0)
  const sumar = (tipo: string, campo: "total" | "fuera_de_servicio") =>
    unidades.reduce(
      (suma, u) => suma + (u.tipos.find((t) => t.tipo_bien === tipo)?.[campo] ?? 0),
      0,
    )

  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-lg font-semibold">Bienes por unidad y fuera de servicio</h2>
      <div className="overflow-x-auto rounded-xs border border-gray-300 bg-white">
        <table className="w-full min-w-[40rem] text-left text-sm">
          <thead>
            <tr className="border-b border-gray-300">
              <th className={claseCabecera}>Unidad</th>
              {tipos.map((tipo) => (
                <th key={tipo} className={`${claseCabecera} text-center`}>
                  {nombreTipoCorto[tipo] ?? tipo}
                </th>
              ))}
              <th className={`${claseCabecera} text-right`}>Total</th>
              <th className={`${claseCabecera} text-right`}>Abiertas</th>
            </tr>
          </thead>
          <tbody>
            {unidades.map((u) => (
              <tr key={u.id} className="border-b border-gray-200">
                <th
                  scope="row"
                  className={`px-3 py-2 ${u.nivel === "OPERACIONAL" ? "pl-6 font-normal" : "font-semibold"}`}
                >
                  {u.nombre}
                </th>
                {u.tipos.map((t) => {
                  const nivel = intensidad(t.total, t.fuera_de_servicio)
                  const marcada =
                    elegida?.unidad.id === u.id && elegida.tipo.tipo_bien === t.tipo_bien
                  return (
                    <td key={t.tipo_bien} className="p-1">
                      <button
                        type="button"
                        aria-pressed={marcada}
                        aria-label={`${u.nombre}, ${nombreTipoCorto[t.tipo_bien] ?? t.tipo_bien}: ${t.total} bienes, ${t.fuera_de_servicio} fuera de servicio`}
                        onClick={() => onElegir({ unidad: u, tipo: t })}
                        style={{ background: fondo(nivel) }}
                        className={`flex min-h-12 w-full flex-col items-center justify-center rounded-xs px-2 py-1 focus-visible:outline-2 focus-visible:outline-foco text-gray-900 ${marcada ? "ring-2 ring-marca" : ""}`}
                      >
                        <span className="font-mono text-base font-medium">{t.total}</span>
                        {t.fuera_de_servicio > 0 && (
                          <span className="text-xs">
                            {t.fuera_de_servicio} <abbr title="Fuera de servicio">F/S</abbr>
                          </span>
                        )}
                      </button>
                    </td>
                  )
                })}
                <td className="px-3 py-2 text-right font-mono">{totalDe(u)}</td>
                <td
                  className={`px-3 py-2 text-right font-mono ${u.abiertas > 0 ? "font-semibold" : "text-gray-500"}`}
                >
                  {u.abiertas}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="bg-gray-50 font-semibold">
              <th scope="row" className="px-3 py-2">
                Total
              </th>
              {tipos.map((tipo) => (
                <td key={tipo} className="px-3 py-2 text-center font-mono">
                  {sumar(tipo, "total")}
                  {sumar(tipo, "fuera_de_servicio") > 0 && (
                    <span className="block text-xs font-normal text-gray-600">
                      {sumar(tipo, "fuera_de_servicio")} F/S
                    </span>
                  )}
                </td>
              ))}
              <td className="px-3 py-2 text-right font-mono">
                {unidades.reduce((suma, u) => suma + totalDe(u), 0)}
              </td>
              <td className="px-3 py-2 text-right font-mono">
                {unidades.reduce((suma, u) => suma + u.abiertas, 0)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}
