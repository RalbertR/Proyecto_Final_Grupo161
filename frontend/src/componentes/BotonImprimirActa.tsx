import { Boton } from "./Boton"
import type { Variante } from "./claseBoton"

type BotonImprimirActaProps = { movimientoId: number; variant?: Variante }

export const BotonImprimirActa = ({
  movimientoId,
  variant = "primario",
}: BotonImprimirActaProps) => (
  <Boton
    type="button"
    variant={variant}
    onClick={() => window.open(`/actas/${movimientoId}/imprimir`, "_blank", "noopener")}
  >
    Imprimir acta
  </Boton>
)
