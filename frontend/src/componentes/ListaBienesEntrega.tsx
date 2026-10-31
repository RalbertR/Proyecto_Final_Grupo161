import { tiposDeBien, type FilaInventario } from "../tipos/bien"
import { Marca } from "./Marca"

type ListaBienesEntregaProps = {
  bienes: FilaInventario[]
  bloqueados: Map<number, string>
  onQuitar: (bienId: number) => void
}

export const ListaBienesEntrega = ({ bienes, bloqueados, onQuitar }: ListaBienesEntregaProps) => (
  <ul className="divide-y divide-gray-100 rounded-xs border border-gray-200">
    {bienes.map((bien) => {
      const motivo = bloqueados.get(bien.bien_id)
      return (
        <li
          key={bien.bien_id}
          className="flex items-center justify-between gap-3 px-3 py-1.5 text-sm"
        >
          <span className={motivo ? "text-gray-400 line-through" : ""}>
            {tiposDeBien[bien.tipo_bien] ?? bien.tipo_bien} ·{" "}
            <span className="font-mono">{bien.identificacion}</span> · {bien.marca} {bien.modelo}
            {bien.ubicacion && <span className="text-gray-500"> · {bien.ubicacion}</span>}
          </span>
          <span className="flex items-center gap-2">
            {motivo && <Marca>{motivo}</Marca>}
            <button
              type="button"
              onClick={() => onQuitar(bien.bien_id)}
              aria-label={`Quitar ${bien.identificacion}`}
              className="inline-flex size-8 items-center justify-center rounded-xs text-lg leading-none text-gray-500 hover:bg-gray-100 hover:text-gray-900 focus-visible:outline-3 focus-visible:outline-foco"
            >
              ×
            </button>
          </span>
        </li>
      )
    })}
  </ul>
)
