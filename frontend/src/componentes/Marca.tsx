import type { ReactNode } from "react"

export type Tono = "pendiente" | "secundario" | "error"

const clasesPorTono: Record<Tono, string> = {
  pendiente: "border-pendiente bg-pendiente/10 text-amber-800",
  secundario: "border-secundario bg-secundario/10 text-slate-700",
  error: "border-error bg-error/5 text-error",
}

export const Marca = ({ children, tono = "pendiente" }: { children: ReactNode; tono?: Tono }) => (
  <span
    className={`inline-flex shrink-0 rounded-xs border px-2 py-0.5 text-xs font-semibold ${clasesPorTono[tono]}`}
  >
    {children}
  </span>
)
