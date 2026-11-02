import type { ReactNode } from "react"
import { fechaLegible, type Movimiento } from "../tipos/movimiento"
import type { ControlRevision, DatoActa } from "../tipos/revision"

type DatosRevisionProps = {
  acta: Movimiento
  control: ControlRevision
  onCambiar: (control: ControlRevision) => void
}

const nombreFila: Record<DatoActa, string> = {
  firmas: "firmas",
  numero_acta: "número de acta",
  fecha_hecho: "fecha del hecho",
  unidades: "unidades",
}

const Anterior = ({
  valor,
  actual,
}: {
  valor: string | null | undefined
  actual: string | null
}) =>
  valor === undefined || valor === actual ? null : (
    <s className="mr-2 text-gray-500">{valor ?? "Sin descripción"}</s>
  )

export const DatosRevision = ({ acta, control, onCambiar }: DatosRevisionProps) => {
  const anterior = acta.versiones.find((v) => v.version === acta.version_vigente - 1)
  const origen = acta.unidad_origen?.nombre
  const destino = acta.unidad_destino?.nombre

  const casilla = (dato: DatoActa, texto: string) => (
    <label className="flex min-h-11 items-center gap-2 text-gray-700">
      <input
        type="checkbox"
        checked={!!control.datos[dato]}
        onChange={(e) =>
          onCambiar({ ...control, datos: { ...control.datos, [dato]: e.target.checked } })
        }
        aria-label={`Coincide con el acta: ${nombreFila[dato]}`}
        className="size-4 accent-marca focus-visible:outline-3 focus-visible:outline-foco"
      />
      {texto}
    </label>
  )

  const filas: { nombre: string; valor: ReactNode; tilde?: ReactNode }[] = [
    {
      nombre: "Firmas",
      valor: destino
        ? `Quien entrega en ${origen} y quien recibe en ${destino}`
        : `Quien firma en ${origen}`,
      tilde: casilla("firmas", "Están en el acta"),
    },
    {
      nombre: "Número de acta",
      valor: (
        <span className="font-mono">
          <Anterior valor={anterior?.numero_acta} actual={acta.numero_acta} />
          {acta.numero_acta}
        </span>
      ),
      tilde: casilla("numero_acta", "Coincide con el acta"),
    },
    {
      nombre: "Fecha del hecho",
      valor: (
        <span className="font-mono">
          <Anterior
            valor={anterior && fechaLegible(anterior.fecha_hecho)}
            actual={fechaLegible(acta.fecha_hecho)}
          />
          {fechaLegible(acta.fecha_hecho)}
        </span>
      ),
      tilde: casilla("fecha_hecho", "Coincide con el acta"),
    },
    {
      nombre: "Unidades",
      valor: destino ? `De ${origen} a ${destino}` : origen,
      tilde: casilla("unidades", "Coincide con el acta"),
    },
    {
      nombre: "Descripción",
      valor: (
        <>
          <Anterior valor={anterior?.descripcion} actual={acta.descripcion} />
          {acta.descripcion ?? <span className="text-gray-500">Sin descripción</span>}
        </>
      ),
    },
    { nombre: "Cargó", valor: <span className="font-mono">{acta.usuario}</span> },
  ]

  return (
    <dl className="divide-y divide-gray-100 text-sm">
      {filas.map((fila) => (
        <div
          key={fila.nombre}
          className="grid gap-x-4 py-1 sm:grid-cols-[10rem_1fr_13rem] sm:items-center"
        >
          <dt className="pt-2 text-xs font-semibold tracking-wide text-gray-500 uppercase sm:pt-0">
            {fila.nombre}
          </dt>
          <dd className="py-1">{fila.valor}</dd>
          <dd>{fila.tilde}</dd>
        </div>
      ))}
    </dl>
  )
}
