import { useQuery } from "@tanstack/react-query"
import { useEffect, useRef } from "react"
import { useParams } from "react-router-dom"
import { obtenerMovimiento } from "../api/movimientos"
import { Boton } from "../componentes/Boton"
import { HojaActa } from "../componentes/HojaActa"
import { hojaDelActa, puedeImprimir } from "../tipos/hoja"

export const ImprimirActaPagina = () => {
  const id = Number(useParams().id)
  const {
    data: acta,
    isError,
    error,
  } = useQuery({
    queryKey: ["movimiento", id],
    queryFn: () => obtenerMovimiento(id),
    retry: false,
    gcTime: 0,
  })
  const imprimio = useRef(false)
  const imprimible = !!acta && puedeImprimir(acta)

  useEffect(() => {
    if (!imprimible) return
    const espera = window.setTimeout(() => {
      document.fonts.ready.then(() => {
        if (imprimio.current) return
        imprimio.current = true
        window.print()
      })
    }, 300)
    return () => window.clearTimeout(espera)
  }, [imprimible])

  const aviso = isError
    ? error.message
    : acta && !imprimible
      ? "Esta acta no tiene una hoja para imprimir desde el sistema."
      : null

  return (
    <div className="min-h-screen bg-fondo text-gray-900 print:bg-white">
      <div className="mx-auto flex max-w-[210mm] flex-col gap-4 px-4 py-6 print:max-w-none print:p-0">
        <div className="flex flex-wrap items-center justify-between gap-3 print:hidden">
          <h1 className="text-lg font-semibold">
            Acta <span className="font-mono">{acta?.numero_acta}</span>
          </h1>
          {imprimible && <Boton onClick={() => window.print()}>Imprimir</Boton>}
        </div>
        {aviso && (
          <p
            role="alert"
            className="rounded-xs border border-error bg-white px-4 py-3 text-sm font-medium text-error"
          >
            {aviso}
          </p>
        )}
        {!acta && !isError && (
          <div aria-busy="true" className="aspect-[210/297] animate-pulse bg-gray-200" />
        )}
        {acta && imprimible && <HojaActa hoja={hojaDelActa(acta)} />}
      </div>
    </div>
  )
}
