import {
  fechaDelTramo,
  posiciones,
  type LineaCustodia as Linea,
  type Tramo,
} from "../tipos/custodia"
import { fechaLegible, hoy } from "../tipos/movimiento"

type Posicion = (hecho: number | null) => number

const claseRotulo =
  "font-etiqueta text-xs font-semibold tracking-wider text-gray-500 uppercase self-center"

const tramos = (lista: { hecho: number | null }[], pos: Posicion) =>
  lista.map((t, i) => {
    const desde = pos(t.hecho)
    const hasta = i + 1 < lista.length ? pos(lista[i + 1].hecho) : 100
    return { izquierda: desde, ancho: hasta - desde }
  })

const colorTramo = (franja: "duena" | "donde" | "estado", t: Tramo, i: number) => {
  if (franja === "estado") return t.alerta ? "bg-error text-white" : "bg-gray-100 text-gray-800"
  if (franja === "duena") return i % 2 ? "bg-gray-700 text-white" : "bg-marca text-white"
  return i % 2 ? "bg-gray-200 text-gray-900" : "bg-gray-100 text-gray-900"
}

const Franja = ({
  rotulo,
  franja,
  lista,
  linea,
  pos,
}: {
  rotulo: string
  franja: "duena" | "donde" | "estado"
  lista: Tramo[]
  linea: Linea
  pos: Posicion
}) => {
  const medidas = tramos(lista, pos)
  return (
    <>
      <span className={claseRotulo}>{rotulo}</span>
      <ol aria-label={rotulo} className="relative h-9">
        {lista.map((t, i) => {
          const fecha = fechaDelTramo(linea, t)
          return (
            <li
              key={i}
              title={t.texto}
              style={{ left: `${medidas[i].izquierda}%`, width: `${medidas[i].ancho}%` }}
              className={`absolute inset-y-0 flex items-center overflow-hidden border-l-2 border-white px-2 text-xs font-medium ${colorTramo(franja, t, i)}`}
            >
              <span className="truncate">{t.texto}</span>
              <span className="sr-only">
                {fecha ? `, desde el ${fechaLegible(fecha)}` : ", desde la carga inicial"}
              </span>
            </li>
          )
        })}
      </ol>
    </>
  )
}

const Eje = ({ linea, pos }: { linea: Linea; pos: Posicion }) => {
  const conCarga = [linea.duena, linea.donde, linea.estado].some((f) => f[0]?.hecho === null)
  let ultima = { x: conCarga ? 0 : -100, fecha: "" }
  const marcas = linea.hechos.flatMap((fecha, i) => {
    const x = pos(i)
    if (fecha === ultima.fecha || x - ultima.x < 10 || x > 88) return []
    ultima = { x, fecha }
    return [{ x, fecha }]
  })
  return (
    <>
      <span aria-hidden="true" />
      <div aria-hidden="true" className="relative h-5 font-mono text-[11px] text-gray-500">
        {conCarga && <span className="absolute left-0">Carga inicial</span>}
        {marcas.map((m) => (
          <span key={m.x} className="absolute pl-1" style={{ left: `${m.x}%` }}>
            {fechaLegible(m.fecha)}
          </span>
        ))}
        <span className="absolute right-0">Hoy</span>
      </div>
    </>
  )
}

export const LineaCustodia = ({
  linea,
  onAbrirActa,
}: {
  linea: Linea
  onAbrirActa: (movimientoId: number) => void
}) => {
  const pos = posiciones(linea, hoy())
  const medidas = tramos(linea.respaldo, pos)
  return (
    <div className="overflow-x-auto">
      <div className="grid min-w-[48rem] grid-cols-[124px_minmax(0,1fr)] gap-x-4 gap-y-1.5">
        <Eje linea={linea} pos={pos} />
        <Franja rotulo="Unidad dueña" franja="duena" lista={linea.duena} linea={linea} pos={pos} />
        <Franja rotulo="Dónde estuvo" franja="donde" lista={linea.donde} linea={linea} pos={pos} />
        <Franja rotulo="Estado" franja="estado" lista={linea.estado} linea={linea} pos={pos} />
        <span className={claseRotulo}>Respaldo</span>
        <ol aria-label="Respaldo" className="relative h-8">
          {linea.respaldo.length === 0 && (
            <li className="absolute inset-y-0 left-0 flex items-center text-xs text-gray-500">
              Sin movimientos registrados
            </li>
          )}
          {linea.respaldo.map((r, i) => (
            <li
              key={r.movimientoId}
              style={{ left: `${medidas[i].izquierda}%`, width: `${medidas[i].ancho}%` }}
              className="absolute inset-y-0 flex items-center overflow-hidden border-l-2 border-gray-400 pl-1.5"
            >
              <button
                type="button"
                onClick={() => onAbrirActa(r.movimientoId)}
                title={r.numeroActa ? `Abrir el acta ${r.numeroActa}` : "Abrir el movimiento"}
                className="truncate font-mono text-xs font-medium underline hover:text-gray-600 focus-visible:outline-2 focus-visible:outline-foco"
              >
                {r.numeroActa ?? "Sin acta"}
              </button>
            </li>
          ))}
        </ol>
      </div>
    </div>
  )
}
