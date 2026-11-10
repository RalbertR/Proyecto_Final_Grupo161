import { Link } from "react-router-dom"
import { haceCuanto, type Pendiente } from "../tipos/pendiente"
import { claseBoton } from "./claseBoton"
import { Marca } from "./Marca"

export const ListaPendientes = ({ pendientes }: { pendientes: Pendiente[] }) => {
  const ahora = new Date()
  return (
    <section
      aria-labelledby="titulo-pendientes"
      className="rounded-xs border border-gray-300 bg-white"
    >
      <header className="flex flex-wrap items-baseline justify-between gap-2 border-b border-gray-200 px-4 py-3">
        <h2 id="titulo-pendientes" className="text-lg font-semibold">
          Para resolver
        </h2>
        <span className="font-etiqueta text-xs font-semibold tracking-wider text-gray-500 uppercase">
          Primero lo más antiguo
        </span>
      </header>
      {pendientes.length === 0 ? (
        <p className="px-4 py-6 text-sm text-gray-600">No hay nada para resolver.</p>
      ) : (
        <ul className="divide-y divide-gray-200">
          {pendientes.map((p) => (
            <li key={p.clave} className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
              <span className="w-36 shrink-0">
                <Marca tono={p.tono}>{p.estado}</Marca>
              </span>
              <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                <p className="font-medium">
                  <span className="font-mono">{p.numero}</span>
                  {p.titulo && <span> {p.titulo}</span>}
                </p>
                <p className="text-sm text-gray-600">
                  {p.detalle} · {haceCuanto(p.fecha, ahora)}
                </p>
              </div>
              <Link
                to={p.ruta}
                state={p.pedido}
                aria-label={`${p.accion} ${p.numero}`}
                className={claseBoton("contorno", "px-3 py-1.5 text-sm")}
              >
                {p.accion}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
