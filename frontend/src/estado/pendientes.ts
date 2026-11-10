import { useQuery } from "@tanstack/react-query"
import { obtenerYo } from "../api/auth"
import { obtenerCambiosObservados } from "../api/cambiosEstado"
import { obtenerDevueltas, obtenerObservados, obtenerPorRecibir } from "../api/movimientos"
import { obtenerBandeja } from "../api/revisiones"

export const usePendientes = () => {
  const yo = useQuery({ queryKey: ["yo"], queryFn: obtenerYo, retry: false })
  const conSesion = !!yo.data
  const corrige = conSesion && yo.data.unidad.nivel !== "DIRECCION"
  const revisa = conSesion && yo.data.unidad.nivel !== "OPERACIONAL"
  const porRecibir = useQuery({
    queryKey: ["por-recibir"],
    queryFn: obtenerPorRecibir,
    enabled: conSesion,
    retry: false,
  })
  const devueltas = useQuery({
    queryKey: ["devueltas"],
    queryFn: obtenerDevueltas,
    enabled: conSesion,
    retry: false,
  })
  const observados = useQuery({
    queryKey: ["observados"],
    queryFn: obtenerObservados,
    enabled: corrige,
    retry: false,
  })
  const cambiosObservados = useQuery({
    queryKey: ["cambios-observados"],
    queryFn: obtenerCambiosObservados,
    enabled: corrige,
    retry: false,
  })
  const aRevisar = useQuery({
    queryKey: ["bandeja"],
    queryFn: obtenerBandeja,
    enabled: revisa,
    retry: false,
  })
  const consultas = [yo, porRecibir, devueltas, observados, cambiosObservados, aRevisar]
  const cargando = consultas.some((consulta) => consulta.isLoading)
  const fallidas = consultas.filter((consulta) => consulta.isError)

  return {
    yo: yo.data,
    porRecibir: porRecibir.data,
    devueltas: devueltas.data,
    observados: observados.data,
    cambiosObservados: cambiosObservados.data,
    aRevisar: aRevisar.data,
    corrige,
    revisa,
    cargando,
    error: fallidas[0]?.error ?? null,
    reintentar: () => fallidas.forEach((consulta) => consulta.refetch()),
  }
}
