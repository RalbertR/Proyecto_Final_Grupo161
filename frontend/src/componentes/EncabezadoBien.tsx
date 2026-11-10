import { nombreEstadoOperativo, tiposDeBien } from "../tipos/bien"
import { fechaDelTramo, type LineaCustodia } from "../tipos/custodia"
import { marcaEvento, type BienHistorial, type EventoHistorial } from "../tipos/historial"
import { fechaLegible } from "../tipos/movimiento"
import { nombreMovimiento } from "../tipos/revision"
import { Dato } from "./Dato"
import { Marca } from "./Marca"

const desde = (fecha: string | null) =>
  fecha ? `Desde el ${fechaLegible(fecha)}` : "Desde la carga inicial"

type EncabezadoBienProps = {
  bien: BienHistorial
  linea: LineaCustodia
  ultimo: EventoHistorial | undefined
}

export const EncabezadoBien = ({ bien, linea, ultimo }: EncabezadoBienProps) => {
  const fueraDeServicio = bien.estado_operativo === "FUERA_DE_SERVICIO"
  const enDotacion = bien.tenencia === "DOTACION"
  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-2">
        <h1 className="font-mono text-3xl leading-tight font-medium tracking-tight">
          {bien.identificacion}
        </h1>
        <p className="text-gray-700">
          {tiposDeBien[bien.tipo_bien] ?? bien.tipo_bien} · {bien.marca} {bien.modelo}
        </p>
        <div className="flex flex-wrap gap-2">
          <Marca tono={fueraDeServicio ? "error" : "secundario"}>
            {nombreEstadoOperativo[bien.estado_operativo]}
          </Marca>
          <Marca tono="secundario">{enDotacion ? "En dotación" : "En depósito"}</Marca>
          {bien.de_baja && <Marca tono="error">De baja</Marca>}
          {bien.con_movimiento_pendiente && <Marca>Movimiento pendiente</Marca>}
        </div>
      </div>
      <dl className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-xs border border-gray-300 bg-white px-4 py-3">
          <Dato etiqueta="Unidad dueña">
            <span className="font-semibold">{bien.unidad}</span>
            <span className="block text-sm text-gray-600">
              {desde(fechaDelTramo(linea, linea.duena.at(-1)))}
            </span>
          </Dato>
        </div>
        <div className="rounded-xs border border-gray-300 bg-white px-4 py-3">
          <Dato etiqueta={enDotacion ? "Lo tiene" : "Está en"}>
            <span className="font-semibold">
              {enDotacion ? bien.oficial : (bien.ubicacion ?? "Sin ubicación")}
            </span>
            <span className="block text-sm text-gray-600">
              {enDotacion && (
                <>
                  Legajo <span className="font-mono">{bien.oficial_legajo}</span> ·{" "}
                </>
              )}
              {desde(fechaDelTramo(linea, linea.donde.at(-1)))}
            </span>
          </Dato>
        </div>
        <div className="rounded-xs border border-gray-300 bg-white px-4 py-3">
          <Dato etiqueta="Último movimiento">
            {ultimo ? (
              <>
                <span className="font-semibold">
                  {nombreMovimiento(
                    ultimo.evento,
                    ultimo.oficial_origen_id !== null,
                    ultimo.oficial_destino_id !== null,
                  )}{" "}
                  · <span className="font-mono">{ultimo.numero_acta ?? "Sin acta"}</span>
                </span>
                <span className="block text-sm text-gray-600">{marcaEvento(ultimo).texto}</span>
              </>
            ) : (
              <span className="font-semibold">Sin movimientos</span>
            )}
          </Dato>
        </div>
      </dl>
    </div>
  )
}
