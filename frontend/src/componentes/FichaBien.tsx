import type { ReactNode } from "react"
import { nombreEstadoOperativo } from "../tipos/bien"
import type { BienHistorial } from "../tipos/historial"

const Dato = ({ etiqueta, children }: { etiqueta: string; children: ReactNode }) => (
  <div className="flex flex-col gap-0.5">
    <dt className="font-mono text-xs tracking-widest text-gray-500 uppercase">{etiqueta}</dt>
    <dd className="font-semibold">{children}</dd>
  </div>
)

export const FichaBien = ({ bien }: { bien: BienHistorial }) => (
  <dl className="grid gap-4 rounded-xs border border-secundario bg-slate-50 px-4 py-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
    <Dato etiqueta="Unidad dueña">{bien.unidad}</Dato>
    <Dato etiqueta="Estado de servicio">{nombreEstadoOperativo[bien.estado_operativo]}</Dato>
    <Dato etiqueta="Tenencia">{bien.tenencia === "DEPOSITO" ? "Depósito" : "Dotación"}</Dato>
    {bien.tenencia === "DEPOSITO" ? (
      <Dato etiqueta="Ubicación">{bien.ubicacion}</Dato>
    ) : (
      <Dato etiqueta="Asignado a">
        <span className="font-mono">{bien.oficial_legajo}</span> · {bien.oficial}
      </Dato>
    )}
  </dl>
)
