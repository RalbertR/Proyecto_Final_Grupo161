import { useQuery } from "@tanstack/react-query"
import { useEffect, useMemo, useState } from "react"
import { obtenerArchivoDocumento, obtenerDocumentos } from "../api/documentos"
import { fechaHoraLegible } from "../tipos/movimiento"

const claseEtiqueta = "font-etiqueta text-xs font-semibold tracking-wider text-gray-500 uppercase"

export const VisorActa = ({ movimientoId }: { movimientoId: number }) => {
  const lista = useQuery({
    queryKey: ["documentos", movimientoId],
    queryFn: () => obtenerDocumentos(movimientoId),
    retry: false,
  })
  const documentos = useMemo(
    () =>
      [...(lista.data?.documentos ?? [])].sort(
        (a, b) => a.fecha_carga.localeCompare(b.fecha_carga) || a.id - b.id,
      ),
    [lista.data],
  )
  const [elegido, setElegido] = useState<number | null>(null)
  const [cantidad, setCantidad] = useState(documentos.length)
  if (documentos.length !== cantidad) {
    setCantidad(documentos.length)
    setElegido(null)
  }
  const actual = documentos.find((d) => d.id === elegido) ?? documentos.at(-1)
  const archivo = useQuery({
    queryKey: ["documento-archivo", movimientoId, actual?.id],
    queryFn: () => obtenerArchivoDocumento(movimientoId, actual!.id),
    enabled: actual !== undefined,
    retry: false,
    staleTime: Infinity,
    gcTime: 0,
  })
  const [vista, setVista] = useState<{ blob: Blob; url: string } | null>(null)

  useEffect(() => {
    if (!archivo.data) return
    const url = URL.createObjectURL(archivo.data)
    setVista({ blob: archivo.data, url })
    return () => URL.revokeObjectURL(url)
  }, [archivo.data])

  const url = vista && vista.blob === archivo.data ? vista.url : null
  const error = lista.isError ? lista.error : archivo.isError ? archivo.error : null

  return (
    <section aria-label="Acta escaneada" className="flex h-full flex-col bg-gray-100">
      <div className="flex min-h-12 flex-wrap items-center justify-between gap-2 border-b border-gray-200 bg-white px-4 py-2">
        <span className={claseEtiqueta}>Acta firmada</span>
        {documentos.length > 1 && actual && (
          <label className="flex items-center gap-2 text-sm">
            <span className="sr-only">PDF que se muestra</span>
            <select
              value={actual.id}
              onChange={(e) => setElegido(Number(e.target.value))}
              className="min-h-9 max-w-72 rounded-xs border border-gray-300 bg-white px-2 py-1 hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco"
            >
              {documentos.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.nombre_original} · {fechaHoraLegible(d.fecha_carga)}
                </option>
              ))}
            </select>
          </label>
        )}
        {documentos.length === 1 && actual && (
          <span className="truncate text-xs text-gray-600">
            {actual.nombre_original} · {fechaHoraLegible(actual.fecha_carga)}
          </span>
        )}
      </div>
      <div className="min-h-0 flex-1">
        {error ? (
          <p
            role="alert"
            className="m-4 rounded-xs border border-error bg-white px-4 py-3 text-sm text-error"
          >
            {error.message}
          </p>
        ) : lista.isPending || (actual && !url) ? (
          <div
            aria-busy="true"
            className="m-4 h-[calc(100%-2rem)] animate-pulse rounded-xs bg-gray-200"
          />
        ) : url ? (
          <iframe key={url} title="Acta escaneada" src={url} className="h-full w-full" />
        ) : (
          <p className="flex h-full items-center justify-center px-6 text-center text-sm text-gray-600">
            Esta acta todavía no tiene el PDF firmado.
          </p>
        )}
      </div>
    </section>
  )
}
