import { useId, useState, type ChangeEvent } from "react"

const maximoBytes = 10 * 1024 * 1024

const errorDelPdf = (archivo: File) => {
  if (
    !archivo.name.toLowerCase().endsWith(".pdf") ||
    (archivo.type && archivo.type !== "application/pdf")
  )
    return "Elegí un archivo PDF."
  if (archivo.size === 0) return "El PDF está vacío."
  if (archivo.size > maximoBytes) return "El PDF no puede superar los 10 MB."
  return null
}

type CampoPdfProps = {
  etiqueta: string
  ayuda: string
  obligatorio?: boolean
  deshabilitado?: boolean
  onElegir: (archivo: File | null) => void
}

export const CampoPdf = ({
  etiqueta,
  ayuda,
  obligatorio = false,
  deshabilitado = false,
  onElegir,
}: CampoPdfProps) => {
  const ayudaId = useId()
  const errorId = useId()
  const [error, setError] = useState<string | null>(null)

  const elegir = (e: ChangeEvent<HTMLInputElement>) => {
    setError(null)
    const elegido = e.currentTarget.files?.[0]
    if (!elegido) {
      onElegir(null)
      return
    }
    const problema = errorDelPdf(elegido)
    if (problema) {
      setError(problema)
      e.currentTarget.value = ""
      onElegir(null)
      return
    }
    onElegir(elegido)
  }

  return (
    <div className="flex min-w-0 flex-col gap-2">
      <label className="flex min-w-0 flex-col gap-2 text-sm font-semibold">
        {etiqueta}
        <input
          type="file"
          accept=".pdf,application/pdf"
          required={obligatorio}
          disabled={deshabilitado}
          aria-describedby={error ? `${ayudaId} ${errorId}` : ayudaId}
          aria-invalid={!!error}
          onChange={elegir}
          className="min-h-11 min-w-0 rounded-xs border border-gray-300 bg-white p-2 font-normal file:mr-3 file:cursor-pointer file:rounded-xs file:border-0 file:bg-gray-100 file:px-3 file:py-1 file:font-semibold hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco disabled:opacity-50"
        />
      </label>
      <p id={ayudaId} className="text-xs text-gray-600">
        {ayuda}
      </p>
      {error && (
        <p
          id={errorId}
          role="alert"
          className="rounded-xs border border-error bg-error/5 px-4 py-3 text-sm text-error"
        >
          {error}
        </p>
      )}
    </div>
  )
}
