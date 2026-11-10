import type { ReactNode } from "react"

export type Tono = "pendiente" | "secundario" | "error" | "observado"

const clasesPorTono: Record<Tono, string> = {
  pendiente: "border-pendiente bg-pendiente/15 text-marca",
  secundario: "border-secundario bg-secundario/10 text-gray-700",
  error: "border-error bg-error/5 text-error",
  observado: "border-observado bg-observado/10 text-observado",
}

export const Marca = ({ children, tono = "pendiente" }: { children: ReactNode; tono?: Tono }) => (
  <span
    className={`inline-flex shrink-0 rounded-xs border px-2 py-0.5 text-xs font-semibold ${clasesPorTono[tono]}`}
  >
    {children}
  </span>
)
