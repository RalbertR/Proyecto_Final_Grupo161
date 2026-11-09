import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useId, useRef, useState } from "react"
import { adjuntarDocumento, obtenerArchivoDocumento, obtenerDocumentos } from "../api/documentos"
import { ErrorHttp } from "../api/http"
import { descargarPdf, type Documento } from "../tipos/documento"
import { fechaHoraLegible } from "../tipos/movimiento"
import { Boton } from "./Boton"
import { CampoPdf } from "./CampoPdf"

const claseError = "rounded-xs border border-error bg-error/5 px-4 py-3 text-sm text-error"
const tamanoLegible = (bytes: number) =>
  bytes < 1024 * 1024
    ? `${Math.max(1, Math.ceil(bytes / 1024))} KB`
    : `${(bytes / (1024 * 1024)).toLocaleString("es-AR", { maximumFractionDigits: 2 })} MB`

export const DocumentosActa = ({ movimientoId }: { movimientoId: number }) => {
  const tituloId = useId()
  const enviando = useRef(false)
  const queryClient = useQueryClient()
  const [archivo, setArchivo] = useState<File | null>(null)
  const [cargas, setCargas] = useState(0)
  const queryKey = ["documentos", movimientoId]
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey,
    queryFn: () => obtenerDocumentos(movimientoId),
    retry: false,
  })
  const subida = useMutation({
    mutationFn: (seleccionado: File) => adjuntarDocumento(movimientoId, seleccionado),
    onSuccess: async () => {
      setArchivo(null)
      setCargas((n) => n + 1)
      await queryClient.invalidateQueries({ queryKey })
    },
    onError: (e) => {
      if (e instanceof ErrorHttp && [403, 404, 409].includes(e.status))
        queryClient.invalidateQueries({ queryKey })
    },
    onSettled: () => {
      enviando.current = false
    },
  })
  const descarga = useMutation({
    mutationFn: async (documento: Documento) =>
      descargarPdf(
        await obtenerArchivoDocumento(movimientoId, documento.id),
        documento.nombre_original,
      ),
  })

  const elegirArchivo = (elegido: File | null) => {
    subida.reset()
    setArchivo(elegido)
  }

  const adjuntar = () => {
    if (!archivo || enviando.current || !data?.puede_adjuntar) return
    enviando.current = true
    subida.mutate(archivo)
  }

  return (
    <section
      aria-labelledby={tituloId}
      className="flex min-w-0 flex-col gap-3 border-t border-gray-200 pt-4"
    >
      <h3 id={tituloId} className="text-sm font-semibold">
        PDFs del acta
      </h3>
      {isPending && (
        <p role="status" className="text-sm text-gray-600">
          Cargando documentos…
        </p>
      )}
      {isError && (
        <div role="alert" className={claseError}>
          <p>{error.message}</p>
          <Boton type="button" variant="contorno" onClick={() => refetch()} className="mt-2">
            Reintentar
          </Boton>
        </div>
      )}
      {data && !isError && (
        <>
          {data.documentos.length === 0 ? (
            <p className="text-sm text-gray-600">Esta acta todavía no tiene PDFs adjuntos.</p>
          ) : (
            <ul className="divide-y divide-gray-100 rounded-xs border border-gray-200">
              {data.documentos.map((documento) => (
                <li
                  key={documento.id}
                  className="flex flex-wrap items-center justify-between gap-3 px-3 py-3 text-sm"
                >
                  <div className="min-w-0 flex-1 basis-48">
                    <p className="break-words font-semibold">{documento.nombre_original}</p>
                    <p className="mt-1 text-xs text-gray-600">
                      {tamanoLegible(documento.tamano_bytes)} · {documento.usuario} ·{" "}
                      {fechaHoraLegible(documento.fecha_carga)}
                    </p>
                  </div>
                  <Boton
                    type="button"
                    variant="contorno"
                    disabled={descarga.isPending}
                    onClick={() => descarga.mutate(documento)}
                  >
                    {descarga.isPending && descarga.variables.id === documento.id
                      ? "Descargando…"
                      : "Descargar PDF"}
                  </Boton>
                </li>
              ))}
            </ul>
          )}
          {data.puede_adjuntar && (
            <div className="flex flex-col gap-2">
              <CampoPdf
                key={cargas}
                etiqueta="Adjuntar PDF firmado"
                ayuda="PDF de hasta 10 MB. Los documentos ya cargados se conservan."
                deshabilitado={subida.isPending}
                onElegir={elegirArchivo}
              />
              <div className="flex justify-end">
                <Boton type="button" onClick={adjuntar} disabled={!archivo || subida.isPending}>
                  {subida.isPending ? "Adjuntando…" : "Adjuntar PDF"}
                </Boton>
              </div>
            </div>
          )}
        </>
      )}
      {subida.error && (
        <p role="alert" className={claseError}>
          {subida.error.message}
        </p>
      )}
      {subida.isSuccess && (
        <p
          role="status"
          className="rounded-xs border border-exito bg-exito/5 px-4 py-3 text-sm text-green-900"
        >
          El PDF quedó adjunto al acta.
        </p>
      )}
      {descarga.error && (
        <p role="alert" className={claseError}>
          {descarga.error.message}
        </p>
      )}
    </section>
  )
}
