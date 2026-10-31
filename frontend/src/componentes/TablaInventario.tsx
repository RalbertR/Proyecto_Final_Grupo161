import { keepPreviousData, useQuery } from "@tanstack/react-query"
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from "@tanstack/react-table"
import { useMemo, useState } from "react"
import { obtenerInventario } from "../api/inventario"
import { motivoBloqueo, tiposDeBien, type FilaInventario } from "../tipos/bien"
import { Boton } from "./Boton"
import { Marca } from "./Marca"

const col = createColumnHelper<FilaInventario>()

const columnas = [
  col.accessor("unidad", { header: "Unidad" }),
  col.accessor("tipo_bien", {
    header: "Tipo",
    cell: (info) => tiposDeBien[info.getValue()] ?? info.getValue(),
  }),
  col.accessor("identificacion", {
    header: "Identificación",
    cell: (info) => <span className="font-mono">{info.getValue()}</span>,
  }),
  col.accessor("marca", { header: "Marca" }),
  col.accessor("modelo", { header: "Modelo" }),
  col.accessor("estado_operativo", {
    header: "Estado operativo",
    cell: (info) => (info.getValue() === "EN_SERVICIO" ? "En servicio" : "Fuera de servicio"),
  }),
  col.accessor("tenencia", {
    header: "Tenencia",
    cell: ({ row: { original: bien } }) => (
      <div className="flex flex-col">
        <span className="font-mono text-xs tracking-widest text-gray-500 uppercase">
          {bien.tenencia === "DEPOSITO" ? "Depósito" : "Dotación"}
        </span>
        {bien.tenencia === "DEPOSITO" ? (
          <span>{bien.ubicacion}</span>
        ) : (
          <span>
            <span className="font-mono">{bien.oficial_legajo}</span> · {bien.oficial}
          </span>
        )}
      </div>
    ),
  }),
  col.accessor("con_movimiento_pendiente", {
    header: "Movimiento",
    cell: (info) => info.getValue() && <Marca>Pendiente</Marca>,
  }),
]

const sinBienes: FilaInventario[] = []

type TablaInventarioProps = {
  tipos: string[]
  mostrarUnidad: boolean
  unidadId?: number
  unidadPropiaId?: number
  seleccion: FilaInventario[]
  onAlternar: (bien: FilaInventario) => void
}

export const TablaInventario = ({
  tipos,
  mostrarUnidad,
  unidadId,
  unidadPropiaId,
  seleccion,
  onAlternar,
}: TablaInventarioProps) => {
  const { data, isPending, isError, error, isFetching, refetch } = useQuery({
    queryKey: ["inventario", unidadId],
    queryFn: () => obtenerInventario(unidadId),
    placeholderData: keepPreviousData,
    retry: false,
  })
  // ponytail: filtra en el cliente porque la API acepta un solo tipo_bien;
  // si la API acepta varios, el filtro pasa a la queryKey.
  const bienes = useMemo(() => {
    const todos = data ?? sinBienes
    return tipos.length ? todos.filter((b) => tipos.includes(b.tipo_bien)) : todos
  }, [data, tipos])
  const elegidos = useMemo(() => new Set(seleccion.map((b) => b.bien_id)), [seleccion])
  const columnasConSeleccion = useMemo(
    () => [
      col.display({
        id: "seleccion",
        header: () => <span className="sr-only">Elegir</span>,
        enableSorting: false,
        cell: ({ row: { original: bien } }) => {
          const motivo = motivoBloqueo(bien, unidadPropiaId)
          return (
            <label title={motivo ?? undefined} className="inline-flex size-6 items-center">
              <input
                type="checkbox"
                checked={elegidos.has(bien.bien_id)}
                disabled={motivo !== null}
                onChange={() => onAlternar(bien)}
                aria-label={motivo ?? `Elegir ${bien.identificacion}`}
                className="size-4 accent-marca focus-visible:outline-3 focus-visible:outline-foco disabled:cursor-not-allowed"
              />
            </label>
          )
        },
      }),
      ...columnas,
    ],
    [elegidos, unidadPropiaId, onAlternar],
  )
  const [sorting, setSorting] = useState<SortingState>([])
  const table = useReactTable({
    data: bienes,
    columns: columnasConSeleccion,
    state: { sorting, columnVisibility: { unidad: mostrarUnidad } },
    onSortingChange: setSorting,
    getRowId: (bien) => String(bien.bien_id),
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

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
      <div role="alert" className="space-y-3 rounded-xs border border-error p-4 text-error">
        <p>{error.message}</p>
        <Boton variant="contorno" onClick={() => refetch()}>
          Reintentar
        </Boton>
      </div>
    )
  if (bienes.length === 0) return <p className="p-4 text-gray-600">No hay bienes para mostrar</p>

  return (
    <div
      aria-busy={isFetching}
      className={`overflow-x-auto transition-opacity ${isFetching ? "opacity-60" : ""}`}
    >
      <table className="w-full text-left text-sm">
        <thead className="border-b border-gray-500">
          {table.getHeaderGroups().map((grupo) => (
            <tr key={grupo.id}>
              {grupo.headers.map((header) => {
                const orden = header.column.getIsSorted()
                return (
                  <th
                    key={header.id}
                    scope="col"
                    aria-sort={
                      orden === "asc" ? "ascending" : orden === "desc" ? "descending" : undefined
                    }
                    className="px-3 py-2 font-semibold whitespace-nowrap"
                  >
                    {!header.isPlaceholder &&
                      (header.column.getCanSort() ? (
                        <button
                          type="button"
                          onClick={header.column.getToggleSortingHandler()}
                          className="inline-flex items-center gap-1 hover:underline focus-visible:outline-3 focus-visible:outline-foco"
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          <span aria-hidden="true">
                            {orden === "asc" ? "▲" : orden === "desc" ? "▼" : ""}
                          </span>
                        </button>
                      ) : (
                        flexRender(header.column.columnDef.header, header.getContext())
                      ))}
                  </th>
                )
              })}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((fila) => (
            <tr
              key={fila.id}
              className={`border-b border-gray-200 ${elegidos.has(fila.original.bien_id) ? "bg-marca/5" : fila.original.con_movimiento_pendiente ? "bg-pendiente/5" : ""}`}
            >
              {fila.getVisibleCells().map((celda) => (
                <td key={celda.id} className="px-3 py-2 align-top">
                  {flexRender(celda.column.columnDef.cell, celda.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
