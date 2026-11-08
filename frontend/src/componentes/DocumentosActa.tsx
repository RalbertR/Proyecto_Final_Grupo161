import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useId, useRef, useState, type ChangeEvent } from "react"
import { adjuntarDocumento, obtenerArchivoDocumento, obtenerDocumentos } from "../api/documentos"
import { ErrorHttp } from "../api/http"
import type { Documento } from "../tipos/documento"
import { fechaHoraLegible } from "../tipos/movimiento"
import { Boton } from "./Boton"

const maximoBytes = 10 * 1024 * 1024
const claseError = "rounded-xs border border-error bg-error/5 px-4 py-3 text-sm text-error"
const tamanoLegible = (bytes: number) =>
  bytes < 1024 * 1024
    ? `${Math.max(1, Math.ceil(bytes / 1024))} KB`
    : `${(bytes / (1024 * 1024)).toLocaleString("es-AR", { maximumFractionDigits: 2 })} MB`

export const DocumentosActa = ({ movimientoId }: { movimientoId: number }) => {
  const tituloId = useId()
  const ayudaId = useId()
  const campoArchivo = useRef<HTMLInputElement>(null)
  const enviando = useRef(false)
  const queryClient = useQueryClient()
  const [archivo, setArchivo] = useState<File | null>(null)
  const [errorLocal, setErrorLocal] = useState<string | null>(null)
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
      if (campoArchivo.current) campoArchivo.current.value = ""
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
    mutationFn: async (documento: Documento) => {
      const contenido = await obtenerArchivoDocumento(movimientoId, documento.id)
      const url = URL.createObjectURL(contenido)
      const enlace = document.createElement("a")
      enlace.href = url
      enlace.download = documento.nombre_original
      document.body.append(enlace)
      enlace.click()
      enlace.remove()
      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    },
  })

  const elegirArchivo = (e: ChangeEvent<HTMLInputElement>) => {
    subida.reset()
    setErrorLocal(null)
    setArchivo(null)
    const elegido = e.currentTarget.files?.[0]
    if (!elegido) return
    if (
      !elegido.name.toLowerCase().endsWith(".pdf") ||
      (elegido.type && elegido.type !== "application/pdf")
    ) {
      setErrorLocal("Elegí un archivo PDF.")
      e.currentTarget.value = ""
      return
    }
    if (elegido.size === 0 || elegido.size > maximoBytes) {
      setErrorLocal(
        elegido.size === 0 ? "El PDF está vacío." : "El PDF no puede superar los 10 MB.",
      )
      e.currentTarget.value = ""
      return
    }
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
              <label className="flex min-w-0 flex-col gap-2 text-sm font-semibold">
                Adjuntar PDF firmado
                <input
                  ref={campoArchivo}
                  type="file"
                  accept=".pdf,application/pdf"
                  disabled={subida.isPending}
                  aria-describedby={ayudaId}
                  onChange={elegirArchivo}
                  className="min-h-11 min-w-0 rounded-xs border border-gray-300 bg-white p-2 font-normal file:mr-3 file:cursor-pointer file:rounded-xs file:border-0 file:bg-gray-100 file:px-3 file:py-1 file:font-semibold hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco disabled:opacity-50"
                />
              </label>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p id={ayudaId} className="text-xs text-gray-600">
                  PDF de hasta 10 MB. Los documentos ya cargados se conservan.
                </p>
                <Boton type="button" onClick={adjuntar} disabled={!archivo || subida.isPending}>
                  {subida.isPending ? "Adjuntando…" : "Adjuntar PDF"}
                </Boton>
              </div>
            </div>
          )}
        </>
      )}
      {(errorLocal || subida.error) && (
        <p role="alert" className={claseError}>
          {errorLocal ?? subida.error?.message}
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
