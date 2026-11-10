import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useRef, useState, type ChangeEvent, type FormEvent } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { obtenerYo } from "../api/auth"
import { obtenerInventario } from "../api/inventario"
import { registrarEntrega } from "../api/movimientos"
import { obtenerDestinos } from "../api/unidades"
import { Boton } from "../componentes/Boton"
import { BotonImprimirActa } from "../componentes/BotonImprimirActa"
import { BuscadorBienes } from "../componentes/BuscadorBienes"
import { claseBoton } from "../componentes/claseBoton"
import { DocumentosActa } from "../componentes/DocumentosActa"
import { HojaActa } from "../componentes/HojaActa"
import { ListaBienesEntrega } from "../componentes/ListaBienesEntrega"
import { areasDe, motivoBloqueo, motivosDeBloqueo, type FilaInventario } from "../tipos/bien"
import { hojaDelActa, renglonHoja, type DatosHoja } from "../tipos/hoja"
import { hoy } from "../tipos/movimiento"

type Llegada = { bienes?: FilaInventario[]; volver?: string } | null

const datosIniciales = () => ({ destino: "", numeroActa: "", fechaHecho: hoy(), descripcion: "" })

type Datos = ReturnType<typeof datosIniciales>

const sinBloqueados = new Map<number, string>()

const sinPropios = new Set<number>()

const claseCampo = "flex flex-col gap-2 text-sm font-semibold"
const claseControl =
  "min-h-11 rounded-xs border border-gray-300 bg-white px-3 py-2 font-normal hover:border-gray-500 focus-visible:outline-3 focus-visible:outline-foco"
const claseTitulo = "font-etiqueta text-xs font-semibold tracking-wider text-gray-500 uppercase"
const claseEnlace =
  "w-fit text-sm font-semibold text-marca underline hover:text-marca-hover focus-visible:outline-3 focus-visible:outline-foco"

export const NuevaEntregaPagina = () => {
  const { state, pathname } = useLocation()
  const llegada = state as Llegada
  const volver = llegada?.volver ?? "/"
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: yo } = useQuery({ queryKey: ["yo"], queryFn: obtenerYo, retry: false })
  const { data: destinos } = useQuery({ queryKey: ["destinos"], queryFn: obtenerDestinos })
  const [bienes, setBienes] = useState<FilaInventario[]>(() => llegada?.bienes ?? [])
  const [bloqueados, setBloqueados] = useState(sinBloqueados)
  const [datos, setDatos] = useState(datosIniciales)
  const enviando = useRef(false)

  const marcarBloqueados = async () => {
    if (!yo) return
    queryClient.invalidateQueries({ queryKey: ["inventario"] })
    const frescas = await queryClient
      .fetchQuery({
        queryKey: ["inventario", yo.unidad.id],
        queryFn: () => obtenerInventario(yo.unidad.id),
      })
      .catch(() => null)
    if (!frescas) return
    setBloqueados(
      motivosDeBloqueo(bienes, frescas, (fresca) =>
        fresca ? motivoBloqueo(fresca, yo.unidad.id) : "Ya no está en el inventario",
      ),
    )
  }

  const {
    mutate,
    isPending,
    isError,
    error,
    data: registrada,
  } = useMutation({
    mutationFn: registrarEntrega,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventario"] })
    },
    onError: marcarBloqueados,
    onSettled: () => {
      enviando.current = false
    },
  })

  const enviables = bienes.filter((b) => !bloqueados.has(b.bien_id))
  const areas = areasDe(enviables)
  const destino = destinos?.find((u) => String(u.id) === datos.destino)

  const cambiar =
    (campo: keyof Datos) =>
    (e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setDatos((actual) => ({ ...actual, [campo]: e.target.value }))

  const handleQuitar = (bienId: number) => {
    setBienes((actual) => actual.filter((b) => b.bien_id !== bienId))
    setBloqueados((actual) => {
      const sin = new Map(actual)
      sin.delete(bienId)
      return sin
    })
  }

  const handleSumar = (bien: FilaInventario) => setBienes((actual) => [...actual, bien])

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (enviando.current) return
    enviando.current = true
    mutate(
      {
        unidad_destino_id: Number(datos.destino),
        numero_acta: datos.numeroActa,
        fecha_hecho: datos.fechaHecho || hoy(),
        descripcion: datos.descripcion.trim() || null,
        bienes: enviables.map((b) => b.bien_id),
      },
      { onSuccess: () => navigate(pathname, { replace: true, state: { volver } }) },
    )
  }

  const inerte = isPending ? "pointer-events-none opacity-50" : ""

  const hoja: DatosHoja = registrada
    ? hojaDelActa(registrada)
    : {
        clase: "ENTREGA",
        numeroActa: datos.numeroActa,
        fechaHecho: datos.fechaHecho,
        unidad: yo?.unidad.nombre ?? "",
        contraparte: destino?.nombre ?? "",
        oficial: null,
        descripcion: datos.descripcion.trim() || null,
        renglones: enviables.map(renglonHoja),
      }

  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <Link
          to={volver}
          aria-disabled={isPending}
          tabIndex={isPending ? -1 : undefined}
          className={`${claseEnlace} ${inerte}`}
        >
          {volver.startsWith("/inventario") ? "Volver al inventario" : "Volver al inicio"}
        </Link>
        <h1 className="text-2xl leading-tight font-semibold tracking-tight">Nueva entrega</h1>
        {yo && <p className="text-sm text-gray-600">Desde {yo.unidad.nombre}</p>}
      </div>
      <div className="grid items-start gap-6 lg:grid-cols-2">
        {registrada ? (
          <div className="flex flex-col gap-4 rounded-xs border border-gray-300 bg-white p-5">
            <p
              role="status"
              className="rounded-xs border border-exito bg-exito/5 px-4 py-3 text-sm font-semibold text-green-900"
            >
              Entrega registrada. Falta imprimir el acta y firmarla.
            </p>
            <div>
              <BotonImprimirActa movimientoId={registrada.id} />
            </div>
            <DocumentosActa movimientoId={registrada.id} />
            <div className="flex flex-wrap gap-4">
              <Link to="/" className={claseEnlace}>
                Volver al inicio
              </Link>
              <Link to="/inventario" className={claseEnlace}>
                Volver al inventario
              </Link>
            </div>
          </div>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="flex flex-col gap-5 rounded-xs border border-gray-300 bg-white p-5"
          >
            {isError && (
              <div
                role="alert"
                className="rounded-xs border border-error bg-error/5 px-4 py-3 text-sm font-medium text-error"
              >
                {error.message}
              </div>
            )}
            <fieldset disabled={isPending} className="flex min-w-0 flex-col gap-5">
              <div className="flex flex-col gap-3">
                <h2 className={claseTitulo}>Datos del acta</h2>
                <label className={claseCampo}>
                  Unidad de destino
                  <select
                    required
                    value={datos.destino}
                    onChange={cambiar("destino")}
                    className={claseControl}
                  >
                    <option value="">Elegí una unidad</option>
                    {destinos?.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.nombre}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className={claseCampo}>
                    Número de acta
                    <input
                      required
                      pattern="[0-9]{4}/[0-9]{4}"
                      placeholder="0001/2026"
                      title="Cuatro dígitos y el año, por ejemplo 0001/2026"
                      value={datos.numeroActa}
                      onChange={cambiar("numeroActa")}
                      className={`${claseControl} font-mono`}
                    />
                    <span className="text-xs font-normal text-gray-500">
                      Cuatro dígitos y el año
                    </span>
                  </label>
                  <label className={claseCampo}>
                    Fecha del hecho
                    <input
                      type="date"
                      required
                      max={hoy()}
                      value={datos.fechaHecho}
                      onChange={cambiar("fechaHecho")}
                      className={`${claseControl} font-mono`}
                    />
                  </label>
                </div>
              </div>
              <div className="flex flex-col gap-3">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h2 className={claseTitulo}>Bienes · {enviables.length}</h2>
                  {areas.length > 0 && (
                    <span className="text-xs text-gray-500">{areas.join(", ")}</span>
                  )}
                </div>
                {bienes.length > 0 ? (
                  <ListaBienesEntrega
                    bienes={bienes}
                    bloqueados={bloqueados}
                    onQuitar={handleQuitar}
                  />
                ) : (
                  <p className="text-sm text-gray-600">
                    Elegí al menos un bien para armar el acta.
                  </p>
                )}
                {yo && (
                  <div className="flex flex-col gap-2 border-t border-gray-200 pt-3">
                    <h3 className="text-sm font-semibold">Agregar del inventario</h3>
                    <BuscadorBienes
                      unidadId={yo.unidad.id}
                      enLista={bienes}
                      propios={sinPropios}
                      onSumar={handleSumar}
                    />
                  </div>
                )}
              </div>
              <div className="flex flex-col gap-3">
                <h2 className={claseTitulo}>Detalle</h2>
                <label className={claseCampo}>
                  Descripción del acta
                  <textarea
                    maxLength={500}
                    rows={3}
                    value={datos.descripcion}
                    onChange={cambiar("descripcion")}
                    className={claseControl}
                  />
                  <span className="text-xs font-normal text-gray-500">
                    Opcional, hasta 500 caracteres
                  </span>
                </label>
              </div>
            </fieldset>
            <div className="flex flex-wrap justify-end gap-2 border-t border-gray-200 pt-4">
              <Link
                to={volver}
                aria-disabled={isPending}
                tabIndex={isPending ? -1 : undefined}
                className={claseBoton("contorno", inerte)}
              >
                Cancelar
              </Link>
              <Boton type="submit" disabled={isPending || enviables.length === 0}>
                {isPending ? "Registrando…" : "Registrar entrega"}
              </Boton>
            </div>
          </form>
        )}
        <div className="flex flex-col gap-2 lg:sticky lg:top-8">
          <h2 className={claseTitulo}>El acta, tal como se imprime</h2>
          <HojaActa hoja={hoja} estado="Pendiente de recepción" />
        </div>
      </div>
    </section>
  )
}
