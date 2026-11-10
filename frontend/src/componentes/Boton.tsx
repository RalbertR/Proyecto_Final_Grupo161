import type { ButtonHTMLAttributes } from "react"
import { claseBoton, type Variante } from "./claseBoton"

type BotonProps = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variante }

export const Boton = ({ variant = "primario", className = "", ...props }: BotonProps) => (
  <button className={claseBoton(variant, className)} {...props} />
)
