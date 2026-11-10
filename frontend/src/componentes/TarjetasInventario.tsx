import type { ResumenTipo } from "../tipos/pendiente"

const Detalle = ({ r }: { r: ResumenTipo }) => {
  if (r.total === 0) return <>Sin bienes</>
  const partes = [
    r.dotacion > 0 && `${r.dotacion} en dotación`,
    r.deposito > 0 && `${r.deposito} en depósito`,
  ].filter(Boolean)
  return (
    <>
      {partes.join(" · ")}
      {r.fueraDeServicio > 0 && (
        <>
          {partes.length > 0 && " · "}
          {r.fueraDeServicio} <abbr title="Fuera de servicio">F/S</abbr>
        </>
      )}
    </>
  )
}

export const TarjetasInventario = ({ resumen }: { resumen: ResumenTipo[] }) => (
  <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
    {resumen.map((r) => (
      <li
        key={r.tipo}
        className="flex flex-col gap-1 rounded-xs border border-gray-300 border-t-marca bg-white px-4 pt-3 pb-4 [border-top-width:3px]"
      >
        <span className="font-etiqueta text-xs font-semibold tracking-wider text-gray-500 uppercase">
          {r.nombre}
        </span>
        <span className="text-3xl font-semibold tracking-tight">{r.total}</span>
        <span className="text-sm text-gray-600">
          <Detalle r={r} />
        </span>
      </li>
    ))}
  </ul>
)
