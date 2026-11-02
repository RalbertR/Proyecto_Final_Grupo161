import type { ReactNode } from "react"

type Tono = "pendiente" | "secundario"

const clasesPorTono: Record<Tono, string> = {
  pendiente: "border-pendiente bg-pendiente/10 text-amber-800",
  secundario: "border-secundario bg-secundario/10 text-slate-700",
}

export const Marca = ({ children, tono = "pendiente" }: { children: ReactNode; tono?: Tono }) => (
  <span
    className={`inline-flex shrink-0 rounded-xs border px-2 py-0.5 text-xs font-semibold ${clasesPorTono[tono]}`}
  >
    {children}
  </span>
)
