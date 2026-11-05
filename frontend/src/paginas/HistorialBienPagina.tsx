import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { Link, useLocation, useParams } from "react-router-dom"
import { obtenerHistorial } from "../api/bienes"
import { Boton } from "../componentes/Boton"
import { FichaBien } from "../componentes/FichaBien"
import { Marca } from "../componentes/Marca"
import { ModalActa } from "../componentes/ModalActa"
import { TablaCambiosEstado } from "../componentes/TablaCambiosEstado"
import { TablaMovimientosBien } from "../componentes/TablaMovimientosBien"
import { tiposDeBien } from "../tipos/bien"

export const HistorialBienPagina = () => {
  const bienId = Number(useParams().id)
  const { state } = useLocation()
  const [actaId, setActaId] = useState<number | null>(null)
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ["historial", bienId],
    queryFn: () => obtenerHistorial(bienId),
    retry: false,
  })

  const volver = (
    <Link
      to={state?.volver ?? "/"}
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

  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-col gap-2 border-b border-gray-200 pb-4">
        {volver}
        <h1 className="flex flex-wrap items-center gap-3 text-2xl leading-tight font-semibold tracking-tight">
          <span>
            {bien.marca} {bien.modelo} <span className="font-mono">{bien.identificacion}</span>
          </span>
          {bien.con_movimiento_pendiente && <Marca>Movimiento pendiente</Marca>}
        </h1>
        <p className="text-sm text-gray-600">{tiposDeBien[bien.tipo_bien] ?? bien.tipo_bien}</p>
      </div>
      <FichaBien bien={bien} />
      <div className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold">Movimientos</h2>
        <TablaMovimientosBien
          eventos={eventos.filter((e) => e.registro === "MOVIMIENTO")}
          onAbrirActa={setActaId}
        />
      </div>
      <div className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold">Estado de servicio</h2>
        <TablaCambiosEstado eventos={eventos.filter((e) => e.registro === "CAMBIO_ESTADO")} />
      </div>
      {actaId !== null && <ModalActa movimientoId={actaId} onCerrar={() => setActaId(null)} />}
    </section>
  )
}
