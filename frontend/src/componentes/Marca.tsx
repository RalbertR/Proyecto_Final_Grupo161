import type { ReactNode } from "react"

export const Marca = ({ children }: { children: ReactNode }) => (
  <span className="inline-flex shrink-0 rounded-xs border border-pendiente bg-pendiente/10 px-2 py-0.5 text-xs font-semibold text-amber-800">
    {children}
  </span>
)
