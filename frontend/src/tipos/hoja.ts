import type { EstadoOperativo } from "./bien"
import type { Movimiento, Oficial } from "./movimiento"

export type ClaseHoja = "ENTREGA" | "DOTACION" | "DEVOLUCION"

export interface RenglonHoja {
  tipoBien: string
  identificacion: string
  marca: string
  modelo: string
  estado: EstadoOperativo
}

export const renglonHoja = (b: {
  tipo_bien: string
  identificacion: string
  marca: string
  modelo: string
  estado_operativo: string
}): RenglonHoja => ({
  tipoBien: b.tipo_bien,
  identificacion: b.identificacion,
  marca: b.marca,
  modelo: b.modelo,
  estado: b.estado_operativo as EstadoOperativo,
})

export const rotuloIdentificacion = (renglones: RenglonHoja[]) => {
  const moviles = renglones.filter((r) => r.tipoBien === "MOVIL").length
  if (moviles === 0) return "N.º de serie"
  if (moviles === renglones.length) return "Dominio"
  return "N.º de serie / Dominio"
}

export interface DatosHoja {
  clase: ClaseHoja
  numeroActa: string
  fechaHecho: string
  unidad: string
  contraparte: string
  oficial: Oficial | null
  descripcion: string | null
  renglones: RenglonHoja[]
}

const meses = [
  "enero",
  "febrero",
  "marzo",
  "abril",
  "mayo",
  "junio",
  "julio",
  "agosto",
  "septiembre",
  "octubre",
  "noviembre",
  "diciembre",
]

export const fechaEnLetras = (fecha: string) => {
  const [anio, mes, dia] = fecha.split("-").map(Number)
  if (!anio || !mes || !dia || mes > 12) return "___"
  return `${dia} de ${meses[mes - 1]} de ${anio}`
}

export const puedeImprimir = (acta: Movimiento) => acta.tipo === "ENTREGA"

export const hojaDelActa = (acta: Movimiento): DatosHoja => {
  const clase: ClaseHoja = acta.oficial_origen
    ? "DEVOLUCION"
    : acta.oficial_destino
      ? "DOTACION"
      : "ENTREGA"
  const oficial = acta.oficial_origen ?? acta.oficial_destino
  return {
    clase,
    numeroActa: acta.numero_acta ?? "",
    fechaHecho: acta.fecha_hecho,
    unidad:
      (clase === "DEVOLUCION" ? acta.unidad_destino?.nombre : acta.unidad_origen?.nombre) ?? "",
    contraparte:
      clase === "ENTREGA" ? (acta.unidad_destino?.nombre ?? "") : (oficial?.nombre ?? ""),
    oficial,
    descripcion: acta.descripcion,
    renglones: acta.bienes.map(renglonHoja),
  }
}
