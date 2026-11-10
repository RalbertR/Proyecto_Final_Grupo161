import { nombreEstadoOperativo } from "../tipos/bien"
import { fechaEnLetras, rotuloIdentificacion, type DatosHoja } from "../tipos/hoja"
import { Marca } from "./Marca"

const titulo: Record<DatosHoja["clase"], string> = {
  ENTREGA: "Acta de entrega",
  DOTACION: "Acta de entrega en dotación",
  DEVOLUCION: "Acta de devolución",
}

const parrafo = (h: DatosHoja) => {
  const fecha = fechaEnLetras(h.fechaHecho)
  const oficial = h.oficial ? `${h.oficial.nombre}, legajo ${h.oficial.legajo}` : "____"
  if (h.clase === "DOTACION")
    return `En la fecha ${fecha}, la ${h.unidad} hace entrega en dotación al oficial ${oficial}, de los bienes que se detallan a continuación, en el estado que se indica para cada uno.`
  if (h.clase === "DEVOLUCION")
    return `En la fecha ${fecha}, el oficial ${oficial}, devuelve a la ${h.unidad} los bienes que se detallan a continuación, en el estado que se indica para cada uno.`
  return `En la fecha ${fecha}, la ${h.unidad} hace entrega a la ${h.contraparte || "____"} de los bienes que se detallan a continuación, en el estado que se indica para cada uno.`
}

const firmas = (h: DatosHoja): [string, string][] =>
  h.clase === "DEVOLUCION"
    ? [
        ["Entrega", h.contraparte],
        ["Recibe", h.unidad],
      ]
    : [
        ["Entrega", h.unidad],
        ["Recibe", h.contraparte],
      ]

export const HojaActa = ({ hoja, estado }: { hoja: DatosHoja; estado?: string }) => (
  <article
    aria-label="Acta, tal como se imprime"
    className="flex aspect-[210/297] w-full flex-col gap-5 border border-gray-300 bg-white p-[7%] font-acta text-[13px] leading-relaxed text-gray-900 shadow-sm print:aspect-auto print:min-h-[267mm] print:border-0 print:p-0 print:text-[11pt] print:shadow-none"
  >
    <header className="flex items-start justify-between gap-4 border-b-2 border-marca pb-3">
      <div className="flex items-center gap-2.5 font-sans">
        <div className="flex flex-col leading-tight">
          <span className="text-[11px] tracking-wider text-gray-600 uppercase">
            Sistema Logístico Policial
          </span>
          <span className="font-semibold">{hoja.unidad}</span>
        </div>
      </div>
      <div className="flex flex-col items-end leading-tight">
        <span className="text-base font-semibold">{titulo[hoja.clase]}</span>
        <span className="font-mono text-sm">N.º {hoja.numeroActa || "____/____"}</span>
      </div>
    </header>
    <p>{parrafo(hoja)}</p>
    <table className="w-full border-collapse text-left">
      <thead>
        <tr className="border-b border-gray-900">
          <th className="w-10 py-1 pr-2 font-semibold">N.º</th>
          <th className="py-1 pr-2 font-semibold">{rotuloIdentificacion(hoja.renglones)}</th>
          <th className="py-1 pr-2 font-semibold">Marca</th>
          <th className="py-1 pr-2 font-semibold">Modelo</th>
          <th className="py-1 font-semibold">Estado</th>
        </tr>
      </thead>
      <tbody>
        {hoja.renglones.length === 0 ? (
          <tr className="border-b border-gray-300">
            <td colSpan={5} className="py-2 text-gray-500">
              Sin bienes
            </td>
          </tr>
        ) : (
          hoja.renglones.map((r, i) => (
            <tr key={r.identificacion} className="border-b border-gray-300">
              <td className="py-1 pr-2">{i + 1}</td>
              <td className="py-1 pr-2 font-mono">{r.identificacion}</td>
              <td className="py-1 pr-2">{r.marca}</td>
              <td className="py-1 pr-2">{r.modelo}</td>
              <td className="py-1">{nombreEstadoOperativo[r.estado]}</td>
            </tr>
          ))
        )}
      </tbody>
    </table>
    {hoja.descripcion && (
      <p>
        <span className="font-semibold">Descripción.</span> {hoja.descripcion}
      </p>
    )}
    <footer className="mt-auto grid grid-cols-2 gap-8 pt-10">
      {firmas(hoja).map(([rol, quien]) => (
        <div
          key={rol}
          className="flex flex-col gap-0.5 border-t border-gray-900 pt-1.5 text-[12px]"
        >
          <span className="font-semibold">
            {rol} · {quien || "____"}
          </span>
          <span className="text-gray-600">Firma, aclaración y legajo</span>
        </div>
      ))}
    </footer>
    {estado && (
      <div className="font-sans print:hidden">
        <Marca>{estado}</Marca>
      </div>
    )}
  </article>
)
