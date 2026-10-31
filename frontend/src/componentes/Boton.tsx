import type { ButtonHTMLAttributes } from "react"

type Variante = "primario" | "secundario" | "contorno" | "claro"

type BotonProps = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variante }

const clasesPorVariante: Record<Variante, string> = {
  primario: "bg-marca text-white hover:bg-marca-hover",
  secundario: "bg-secundario text-white",
  contorno: "border border-gray-500 bg-transparent hover:border-current",
  claro: "bg-white text-marca hover:bg-gray-100",
}

export const Boton = ({ variant = "primario", className = "", ...props }: BotonProps) => (
  <button
    className={`inline-flex items-center justify-center gap-2 rounded-xs px-4 py-2 font-semibold transition active:scale-95 focus-visible:outline-3 focus-visible:outline-foco disabled:cursor-not-allowed disabled:opacity-50 ${clasesPorVariante[variant]} ${className}`}
    {...props}
  />
)
