import type { Tono } from "../componentes/Marca"
import { areasDe, nombreEstadoOperativo, tiposDeBien, type FilaInventario } from "./bien"
import { ultimaObservacionCambio, type CambioEstado } from "./cambioEstado"
import { devoluciones, ultimaObservacion, type Movimiento } from "./movimiento"
import {
  extremosActa,
  extremosDelActa,
  nombreDelActa,
  nombreMovimiento,
  type RegistroBandeja,
} from "./revision"

export type Registro = "MOVIMIENTO" | "CAMBIO_ESTADO"

export interface PedidoAbrir {
  abrir: number
  registro: Registro
}

export interface Pendiente {
  clave: string
  estado: string
  tono: Tono
  fecha: string
  numero: string
  titulo: string
  detalle: string
  accion: string
  ruta: string
  pedido: PedidoAbrir
}

type Fuentes = {
  observados?: Movimiento[]
  devueltas?: Movimiento[]
  porRecibir?: Movimiento[]
  cambiosObservados?: CambioEstado[]
  aRevisar?: RegistroBandeja[]
}

const conHora = (fecha: string) => fecha.length > 10

export const instante = (fecha: string) =>
  conHora(fecha) ? new Date(`${fecha}Z`) : new Date(`${fecha}T00:00:00`)

const describir = (...partes: (string | null | undefined | false)[]) =>
  partes.filter(Boolean).join(" ")

const mayor = (fechas: string[]) => fechas.reduce((a, b) => (instante(a) >= instante(b) ? a : b))

const aCambio = (estado: keyof typeof nombreEstadoOperativo) =>
  `Cambio a ${nombreEstadoOperativo[estado].toLowerCase()}`

const deMovimiento = (
  m: Movimiento,
  estado: string,
  tono: Tono,
  fecha: string,
  titulo: string,
  detalle: string,
  accion: string,
  ruta: string,
): Pendiente => ({
  clave: `${estado}-${m.id}`,
  estado,
  tono,
  fecha,
  numero: m.numero_acta ?? "",
  titulo,
  detalle,
  accion,
  ruta,
  pedido: { abrir: m.id, registro: "MOVIMIENTO" },
})

export const armarPendientes = (f: Fuentes): Pendiente[] =>
  [
    ...(f.observados ?? []).map((m) =>
      deMovimiento(
        m,
        "Observada",
        "observado",
        ultimaObservacion(m)?.fecha ?? m.fecha_carga,
        ultimaObservacion(m)?.motivo_observacion ?? "",
        describir(
          nombreDelActa(m),
          extremosDelActa(m).destino && `a ${extremosDelActa(m).destino}`,
        ),
        "Corregir",
        "/observados",
      ),
    ),
    ...(f.devueltas ?? []).map((m) =>
      deMovimiento(
        m,
        "Devuelta",
        "observado",
        devoluciones(m)[0]?.fecha ?? m.fecha_carga,
        devoluciones(m)[0]?.motivo ?? "",
        `${m.unidad_destino?.nombre ?? "El destino"} la devolvió`,
        "Corregir",
        "/devueltas",
      ),
    ),
    ...(f.porRecibir ?? []).map((m) =>
      deMovimiento(
        m,
        "Por recibir",
        "pendiente",
        mayor([m.fecha_carga, ...m.versiones.map((v) => v.fecha)]),
        `De ${extremosDelActa(m).origen}`,
        `${m.bienes.length === 1 ? "1 bien" : `${m.bienes.length} bienes`} · ${areasDe(m.bienes).join(", ")}`,
        "Controlar",
        "/por-recibir",
      ),
    ),
    ...(f.cambiosObservados ?? []).map((c): Pendiente => ({
      clave: `Cambio observado-${c.id}`,
      estado: "Cambio observado",
      tono: "observado",
      fecha: ultimaObservacionCambio(c)?.fecha ?? c.fecha,
      numero: c.bien.identificacion,
      titulo: ultimaObservacionCambio(c)?.motivo_observacion ?? "",
      detalle: describir(`${c.bien.marca} ${c.bien.modelo}`, "·", aCambio(c.estado_nuevo)),
      accion: "Corregir",
      ruta: "/observados",
      pedido: { abrir: c.id, registro: "CAMBIO_ESTADO" },
    })),
    ...(f.aRevisar ?? []).map((r): Pendiente => {
      const cambio = r.registro === "CAMBIO_ESTADO"
      const extremos = extremosActa(
        r.evento,
        r.unidad_origen,
        r.unidad_destino,
        r.oficial_origen,
        r.oficial_destino,
      )
      return {
        clave: `Para revisar-${r.registro}-${r.registro_id}`,
        estado: "Para revisar",
        tono: "pendiente",
        fecha: r.fecha,
        numero: r.numero_acta ?? r.bien_identificacion ?? "",
        titulo:
          cambio && r.estado_nuevo
            ? aCambio(r.estado_nuevo)
            : describir(
                nombreMovimiento(r.evento, r.oficial_origen !== null, r.oficial_destino !== null),
                extremos.origen && `de ${extremos.origen}`,
                extremos.destino && `a ${extremos.destino}`,
              ),
        detalle: `Registrado por ${r.unidad_registrante}`,
        accion: "Revisar",
        ruta: "/revision",
        pedido: { abrir: r.registro_id, registro: cambio ? "CAMBIO_ESTADO" : "MOVIMIENTO" },
      }
    }),
  ].sort((a, b) => instante(a.fecha).getTime() - instante(b.fecha).getTime())

export interface ResumenTipo {
  tipo: string
  nombre: string
  total: number
  dotacion: number
  deposito: number
  fueraDeServicio: number
}

const nombreCorto: Record<string, string> = {
  ARMAMENTO: "Armamento",
  CHALECO: "Chalecos",
  MOVIL: "Móviles",
  EQUIPO_COMUNICACIONES: "Comunicaciones",
}

export const resumenPorTipo = (filas: FilaInventario[]): ResumenTipo[] =>
  Object.keys(tiposDeBien).map((tipo) => {
    const delTipo = filas.filter((f) => f.tipo_bien === tipo)
    return {
      tipo,
      nombre: nombreCorto[tipo] ?? tiposDeBien[tipo],
      total: delTipo.length,
      dotacion: delTipo.filter((f) => f.tenencia === "DOTACION").length,
      deposito: delTipo.filter((f) => f.tenencia === "DEPOSITO").length,
      fueraDeServicio: delTipo.filter((f) => f.estado_operativo === "FUERA_DE_SERVICIO").length,
    }
  })

const inicioDelDia = (fecha: Date) =>
  new Date(fecha.getFullYear(), fecha.getMonth(), fecha.getDate()).getTime()

export const haceCuanto = (fecha: string, ahora: Date) => {
  const momento = instante(fecha)
  const dias = Math.round((inicioDelDia(ahora) - inicioDelDia(momento)) / 86_400_000)
  if (dias <= 0)
    return conHora(fecha)
      ? `hoy a las ${momento.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit", hour12: false })}`
      : "hoy"
  if (dias === 1) return "ayer"
  return `hace ${dias} días`
}

const enLetras = ["Dos", "Tres", "Cuatro", "Cinco", "Seis", "Siete", "Ocho", "Nueve", "Diez"]

export const tituloInicio = (cantidad: number) => {
  if (cantidad === 0) return "No hay nada pendiente"
  if (cantidad === 1) return "Un pendiente espera a tu unidad"
  return `${enLetras[cantidad - 2] ?? cantidad} pendientes esperan a tu unidad`
}

export const fechaDeHoyEnLetras = (ahora: Date) => {
  const texto = ahora
    .toLocaleDateString("es-AR", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    })
    .replace(",", "")
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}
