import type { ReactNode } from "react"

export const Dato = ({ etiqueta, children }: { etiqueta: string; children: ReactNode }) => (
  <div className="flex flex-col gap-0.5">
    <dt className="font-mono text-xs font-normal tracking-widest text-gray-500 uppercase">
      {etiqueta}
    </dt>
    <dd>{children}</dd>
  </div>
)
