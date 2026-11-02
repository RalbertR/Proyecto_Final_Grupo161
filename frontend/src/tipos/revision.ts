import type { Movimiento } from "./movimiento"

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
}

export const nombreEvento: Record<string, string> = {
  ALTA: "Alta",
  ENTREGA: "Entrega",
  REUBICACION: "Reubicación",
  TRASLADO: "Traslado",
  BAJA: "Baja",
}

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
  accion: "Observada" | "Revisada" | "Corregida"
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
  ].sort((a, b) => a.fecha.localeCompare(b.fecha))
