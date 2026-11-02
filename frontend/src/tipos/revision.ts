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
