import { useEffect } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import type { PedidoAbrir, Registro } from "../tipos/pendiente"

export const fresca = <T>(lista: T[] | undefined, despuesDeMontar: boolean, cargando: boolean) =>
  despuesDeMontar && !cargando ? lista : undefined

export const porId = (item: { id: number }) => item.id

export const porRegistroId = (item: { registro_id: number }) => item.registro_id

export const useAbrirDesdeInicio = <T>(
  lista: T[] | undefined,
  registro: Registro,
  id: (item: T) => number,
  abrir: (item: T) => void,
) => {
  const { state, pathname, search } = useLocation()
  const navigate = useNavigate()
  const pedido = state as PedidoAbrir | null

  useEffect(() => {
    if (!lista || pedido?.registro !== registro) return
    const item = lista.find((i) => id(i) === pedido.abrir)
    if (item) abrir(item)
    navigate(pathname + search, { replace: true, state: null })
  }, [lista, pedido, registro, id, abrir, navigate, pathname, search])
}
