import { nombreEstadoOperativo, type EstadoOperativo } from "./bien"
import { estadoOpuesto } from "./cambioEstado"
import type { BienHistorial, EventoHistorial } from "./historial"

export interface Tramo {
  hecho: number | null
  texto: string
  alerta: boolean
}

export interface MarcaRespaldo {
  hecho: number
  numeroActa: string | null
  movimientoId: number
}

export interface LineaCustodia {
  hechos: string[]
  duena: Tramo[]
  donde: Tramo[]
  estado: Tramo[]
  respaldo: MarcaRespaldo[]
}

const tramo = (hecho: number | null, texto: string, alerta = false): Tramo => ({
  hecho,
  texto,
  alerta,
})

const tramoEstado = (hecho: number | null, estado: EstadoOperativo) =>
  tramo(hecho, nombreEstadoOperativo[estado], estado === "FUERA_DE_SERVICIO")

const dondeDe = (e: EventoHistorial, lado: "origen" | "destino") =>
  (lado === "origen"
    ? (e.oficial_origen ?? e.ubicacion_origen)
    : (e.oficial_destino ?? e.ubicacion_destino)) ?? "Sin ubicación"

export const lineaCustodia = (bien: BienHistorial, eventos: EventoHistorial[]): LineaCustodia => {
  const vigentes = eventos.filter((e) => e.estado === "APLICADO")
  const movimientos = vigentes.filter((e) => e.registro === "MOVIMIENTO")
  const cambios = vigentes.filter((e) => e.registro === "CAMBIO_ESTADO")
  const primero = movimientos[0]
  const alta = vigentes[0]?.registro === "MOVIMIENTO" && vigentes[0].evento === "ALTA"
  const inicio = alta ? 0 : null
  const estadoInicial = cambios[0]?.estado_operativo_nuevo
    ? estadoOpuesto(cambios[0].estado_operativo_nuevo)
    : bien.estado_operativo

  const linea: LineaCustodia = {
    hechos: vigentes.map((e) => e.fecha),
    duena: [
      tramo(
        inicio,
        alta ? (primero.unidad_duena ?? bien.unidad) : (primero?.unidad_origen ?? bien.unidad),
      ),
    ],
    donde: [
      tramo(
        inicio,
        alta
          ? dondeDe(primero, "destino")
          : primero
            ? dondeDe(primero, "origen")
            : (bien.oficial ?? bien.ubicacion ?? "Sin ubicación"),
      ),
    ],
    estado: [tramoEstado(inicio, estadoInicial)],
    respaldo: [],
  }

  vigentes.forEach((e, i) => {
    if (e.registro === "CAMBIO_ESTADO") {
      if (e.estado_operativo_nuevo) linea.estado.push(tramoEstado(i, e.estado_operativo_nuevo))
      return
    }
    linea.respaldo.push({ hecho: i, numeroActa: e.numero_acta, movimientoId: e.registro_id })
    if (alta && i === 0) return
    const duena = e.unidad_duena ?? bien.unidad
    if (linea.duena.at(-1)?.texto !== duena) linea.duena.push(tramo(i, duena))
    linea.donde.push(tramo(i, e.evento === "BAJA" ? "De baja" : dondeDe(e, "destino")))
  })

  return linea
}

const DIA = 86_400_000

const dias = (desde: string, hasta: string) => (Date.parse(hasta) - Date.parse(desde)) / DIA

const CARGA_INICIAL = 14

export const posiciones = (linea: LineaCustodia, hoy: string) => {
  const { hechos } = linea
  if (hechos.length === 0) return () => 0
  const conCarga = [linea.duena, linea.donde, linea.estado].some((f) => f[0]?.hecho === null)
  const inicio = conCarga ? CARGA_INICIAL : 0
  const piso = Math.min(0.1, 0.6 / hechos.length)
  const resto = 1 - piso * hechos.length
  const lapsos = hechos.map((f, i) => Math.max(dias(f, hechos[i + 1] ?? hoy), 0))
  const totalDias = lapsos.reduce((a, b) => a + b, 0)
  const partes = lapsos.map(
    (d) => piso + (totalDias > 0 ? (resto * d) / totalDias : resto / hechos.length),
  )
  const acumulado = partes.map((_, i) => partes.slice(0, i).reduce((a, b) => a + b, 0))
  return (hecho: number | null) => (hecho === null ? 0 : inicio + (100 - inicio) * acumulado[hecho])
}

export const fechaDelTramo = (linea: LineaCustodia, t: Tramo | undefined) =>
  t === undefined || t.hecho === null ? null : linea.hechos[t.hecho]
