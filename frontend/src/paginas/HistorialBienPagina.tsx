import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { Link, useLocation, useParams } from "react-router-dom"
import { obtenerYo } from "../api/auth"
import { obtenerHistorial } from "../api/bienes"
import { Boton } from "../componentes/Boton"
import { EncabezadoBien } from "../componentes/EncabezadoBien"
import { LineaCustodia } from "../componentes/LineaCustodia"
import { ModalActa } from "../componentes/ModalActa"
import { ModalCambioEstado } from "../componentes/ModalCambioEstado"
import { TablaCambiosEstado } from "../componentes/TablaCambiosEstado"
import { TablaMovimientosBien } from "../componentes/TablaMovimientosBien"
import { lineaCustodia } from "../tipos/custodia"

export const HistorialBienPagina = () => {
  const bienId = Number(useParams().id)
  const { state } = useLocation()
  const [actaId, setActaId] = useState<number | null>(null)
  const [cambiando, setCambiando] = useState(false)
  const { data: yo } = useQuery({ queryKey: ["yo"], queryFn: obtenerYo, retry: false })
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ["historial", bienId],
    queryFn: () => obtenerHistorial(bienId),
    retry: false,
  })

  const volver = (
    <Link
      to={state?.volver ?? "/inventario"}
      className="w-fit text-sm font-semibold text-marca underline hover:text-marca-hover focus-visible:outline-3 focus-visible:outline-foco"
    >
      Volver al inventario
    </Link>
  )

  if (isPending)
    return (
      <div aria-busy="true" className="space-y-2">
        {[1, 2, 3, 4].map((n) => (
          <div key={n} className="h-10 animate-pulse rounded-xs bg-gray-200" />
        ))}
      </div>
    )
  if (isError)
    return (
      <section className="flex flex-col gap-4">
        {volver}
        <div role="alert" className="space-y-3 rounded-xs border border-error p-4 text-error">
          <p>{error.message}</p>
          <Boton variant="contorno" onClick={() => refetch()}>
            Reintentar
          </Boton>
        </div>
      </section>
    )

  const { bien, eventos } = data
  const puedeCambiar =
    bien.unidad_id === yo?.unidad.id && !bien.con_movimiento_pendiente && !bien.de_baja

  const linea = lineaCustodia(bien, eventos)
  const ultimo = eventos
    .filter((e) => e.registro === "MOVIMIENTO" && e.estado === "APLICADO")
    .at(-1)

  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-col gap-3">
        {volver}
        <EncabezadoBien bien={bien} linea={linea} ultimo={ultimo} />
      </div>
      <section
        aria-labelledby="titulo-custodia"
        className="flex flex-col gap-3 rounded-xs border border-gray-300 bg-white px-4 py-4"
      >
        <h2 id="titulo-custodia" className="text-lg font-semibold">
          Línea de custodia
        </h2>
        <LineaCustodia linea={linea} onAbrirActa={setActaId} />
      </section>
      <div className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold">Movimientos</h2>
        <TablaMovimientosBien
          eventos={eventos.filter((e) => e.registro === "MOVIMIENTO")}
          onAbrirActa={setActaId}
        />
      </div>
      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-semibold">Estado de servicio</h2>
          {puedeCambiar && (
            <Boton
              variant="contorno"
              onClick={() => setCambiando(true)}
              className="px-3 py-1.5 text-sm"
            >
              Cambiar estado
            </Boton>
          )}
        </div>
        <TablaCambiosEstado
          bien={bien}
          eventos={eventos.filter((e) => e.registro === "CAMBIO_ESTADO")}
        />
      </div>
      {actaId !== null && <ModalActa movimientoId={actaId} onCerrar={() => setActaId(null)} />}
      {cambiando && <ModalCambioEstado bien={bien} onCerrar={() => setCambiando(false)} />}
    </section>
  )
}
