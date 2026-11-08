import { tiposDeBien } from "./bien"
import type { Movimiento, Oficial } from "./movimiento"

export interface RegistroBandeja {
  registro: string
  registro_id: number
  evento: string
  fecha: string
  unidad_registrante: string
  usuario: string
  detalle: string | null
  version: number
  numero_acta: string | null
  unidad_origen: string | null
  unidad_destino: string | null
  oficial_origen: Oficial | null
  oficial_destino: Oficial | null
}

export const nombreEvento: Record<string, string> = {
  ALTA: "Alta",
  ENTREGA: "Entrega",
  REUBICACION: "Reubicación",
  TRASLADO: "Traslado",
  BAJA: "Baja",
}

export const textoOficial = (oficial: Oficial) => `${oficial.legajo} · ${oficial.nombre}`

export const nombreMovimiento = (
  tipo: string,
  conOficialOrigen: boolean,
  conOficialDestino: boolean,
) => {
  if (tipo === "ENTREGA" && conOficialOrigen) return "Devolución"
  if (tipo === "ENTREGA" && conOficialDestino) return "Dotación"
  return nombreEvento[tipo] ?? tipo
}

export const extremosActa = (
  tipo: string,
  unidadOrigen: string | null | undefined,
  unidadDestino: string | null | undefined,
  oficialOrigen: Oficial | null,
  oficialDestino: Oficial | null,
) => {
  if (tipo === "ENTREGA" && oficialOrigen)
    return { origen: textoOficial(oficialOrigen), destino: unidadDestino ?? null }
  if (tipo === "ENTREGA" && oficialDestino)
    return { origen: unidadOrigen ?? null, destino: textoOficial(oficialDestino) }
  return { origen: unidadOrigen ?? null, destino: unidadDestino ?? null }
}

export const conOficial = (acta: Movimiento) =>
  acta.tipo === "ENTREGA" && (acta.oficial_origen !== null || acta.oficial_destino !== null)

export const nombreDelActa = (acta: Movimiento) =>
  nombreMovimiento(acta.tipo, acta.oficial_origen !== null, acta.oficial_destino !== null)

export const extremosDelActa = (acta: Movimiento) =>
  extremosActa(
    acta.tipo,
    acta.unidad_origen?.nombre,
    acta.unidad_destino?.nombre,
    acta.oficial_origen,
    acta.oficial_destino,
  )

export type RevisionCreate =
  | { resultado: "REVISADO"; version: number }
  | { resultado: "OBSERVADO"; motivo_observacion: string; version: number }

export type DatoActa = "firmas" | "numero_acta" | "fecha_hecho" | "unidades"

export const datosActa: DatoActa[] = ["firmas", "numero_acta", "fecha_hecho", "unidades"]

export interface ControlRevision {
  version: number
  datos: Partial<Record<DatoActa, boolean>>
  bienes: Record<number, boolean>
}

export const controlVigente = (
  control: ControlRevision | undefined,
  version: number,
): ControlRevision => (control?.version === version ? control : { version, datos: {}, bienes: {} })

export interface EventoActa {
  accion: "Observada" | "Revisada" | "Corregida" | "Devuelta"
  usuario: string
  fecha: string
  motivo: string | null
}

export const historialActa = (acta: Movimiento): EventoActa[] =>
  [
    ...acta.revisiones.map((r): EventoActa => ({
      accion: r.resultado === "OBSERVADO" ? "Observada" : "Revisada",
      usuario: r.usuario,
      fecha: r.fecha,
      motivo: r.motivo_observacion,
    })),
    ...acta.versiones
      .filter((v) => v.version > 0)
      .map((v): EventoActa => ({
        accion: "Corregida",
        usuario: v.usuario,
        fecha: v.fecha,
        motivo: v.motivo,
      })),
    ...acta.recepciones
      .filter((r) => r.resultado === "DEVUELTO")
      .map((r): EventoActa => ({
        accion: "Devuelta",
        usuario: r.usuario,
        fecha: r.fecha,
        motivo: r.motivo,
      })),
  ].sort((a, b) => a.fecha.localeCompare(b.fecha))

export const nombreDato: Record<DatoActa, string> = {
  firmas: "firmas",
  numero_acta: "número de acta",
  fecha_hecho: "fecha del hecho",
  unidades: "unidades",
}

export const nombreDatoDe = (acta: Movimiento, dato: DatoActa) =>
  dato === "unidades" && conOficial(acta) ? "oficial y unidad" : nombreDato[dato]

export const motivoObservacion = (acta: Movimiento, control: ControlRevision) => {
  const sinTildar = [
    ...datosActa.filter((dato) => !control.datos[dato]).map((dato) => nombreDatoDe(acta, dato)),
    ...acta.bienes
      .filter((bien) => !control.bienes[bien.bien_id])
      .map((bien) => `${tiposDeBien[bien.tipo_bien] ?? bien.tipo_bien} ${bien.identificacion}`),
  ]
  const tildados = datosActa.length + acta.bienes.length - sinTildar.length
  if (tildados === 0 || sinTildar.length === 0) return ""
  return `No coincide con el acta: ${sinTildar.join(", ")}. `.slice(0, 500)
}
