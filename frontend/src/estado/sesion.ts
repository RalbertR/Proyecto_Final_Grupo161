import { create } from "zustand"
import { persist } from "zustand/middleware"

type SesionEstado = {
  token: string | null
  iniciar: (token: string) => void
  cerrar: () => void
}

// persist guarda el token en localStorage: la sesion sobrevive al F5.
export const useSesion = create<SesionEstado>()(
  persist(
    (set) => ({
      token: null,
      iniciar: (token) => set({ token }),
      cerrar: () => set({ token: null }),
    }),
    { name: "sesion" },
  ),
)
