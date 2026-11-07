import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { obtenerInventario } from "../api/inventario"
import { motivoParaSumar, tiposDeBien, type BienActa, type FilaInventario } from "../tipos/bien"
import { Boton } from "./Boton"

const maximoResultados = 8

type BuscadorBienesProps = {
  unidadId: number
  enLista: BienActa[]
  propios: Set<number>
  onSumar: (bien: FilaInventario) => void
}

export const BuscadorBienes = ({ unidadId, enLista, propios, onSumar }: BuscadorBienesProps) => {
  const [texto, setTexto] = useState("")
  const { data: inventario, isError } = useQuery({
    queryKey: ["inventario", unidadId],
    queryFn: () => obtenerInventario(unidadId),
    retry: false,
  })
  const buscado = texto.trim().toLowerCase()
  const buscando = buscado.length >= 2
  const enActa = new Set(enLista.map((b) => b.bien_id))
  const resultados =
    buscando && inventario
      ? inventario
          .filter((b) => !enActa.has(b.bien_id) && b.identificacion.toLowerCase().includes(buscado))
          .slice(0, maximoResultados)
      : []

  const handleSumar = (bien: FilaInventario) => {
    onSumar(bien)
    setTexto("")
  }

  return (
    <div className="flex flex-col gap-2">
      <label className="flex flex-col gap-2 text-sm font-semibold">
        Sumar un bien
        <input
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") e.preventDefault()
          }}
          placeholder="Número de serie o dominio"
          className="min-h-11 rounded-xs border border-gray-300 bg-white px-3 py-2 font-mono font-normal hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco"
        />
      </label>
      {isError ? (
        <p role="alert" className="text-sm text-error">
          No se pudo cargar el inventario
        </p>
      ) : (
        buscando &&
        inventario &&
        (resultados.length === 0 ? (
          <p className="text-sm text-gray-600">No hay bienes con esa identificación</p>
        ) : (
          <ul className="divide-y divide-gray-100 rounded-xs border border-gray-200">
            {resultados.map((bien) => {
              const motivo = motivoParaSumar(bien, unidadId, enLista, propios)
              return (
                <li
                  key={bien.bien_id}
                  className="flex items-center justify-between gap-3 px-3 py-1.5 text-sm"
                >
                  <span className={motivo ? "text-gray-400" : ""}>
                    {tiposDeBien[bien.tipo_bien] ?? bien.tipo_bien} ·{" "}
                    <span className="font-mono">{bien.identificacion}</span> · {bien.marca}{" "}
                    {bien.modelo}
                    {bien.ubicacion && <span className="text-gray-500"> · {bien.ubicacion}</span>}
                  </span>
                  {motivo ? (
                    <span className="shrink-0 text-xs text-gray-500">{motivo}</span>
                  ) : (
                    <Boton
                      type="button"
                      variant="contorno"
                      onClick={() => handleSumar(bien)}
                      aria-label={`Sumar ${bien.identificacion}`}
                      className="shrink-0 px-3 py-1 text-sm"
                    >
                      Sumar
                    </Boton>
                  )}
                </li>
              )
            })}
          </ul>
        ))
      )}
      <span className="text-xs text-gray-500">
        Busca entre los bienes de tu unidad. Solo se suman los que están en depósito y libres, de la
        misma área del acta.
      </span>
    </div>
  )
}
