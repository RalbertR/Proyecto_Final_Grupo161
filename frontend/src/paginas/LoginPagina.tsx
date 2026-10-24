import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { FormEvent } from "react"
import { useNavigate } from "react-router-dom"
import { iniciarSesion } from "../api/auth"
import { Boton } from "../componentes/Boton"
import { Escudo } from "../componentes/Escudo"
import { useSesion } from "../estado/sesion"

export const LoginPagina = () => {
  const queryClient = useQueryClient()
  const iniciar = useSesion((s) => s.iniciar)
  const navigate = useNavigate()
  const { mutate, isPending, isError, error } = useMutation({
    mutationFn: iniciarSesion,
    onSuccess: ({ access_token, usuario }) => {
      queryClient.clear()
      iniciar(access_token)
      queryClient.setQueryData(["yo"], usuario)
      navigate("/", { replace: true })
    },
  })

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    mutate({ usuario: String(fd.get("usuario")), contrasena: String(fd.get("contrasena")) })
  }

  const claseInput = `min-h-11 w-full rounded-xs border px-3 py-2 font-mono text-sm focus:border-gray-900 focus:outline-3 focus:outline-foco disabled:bg-gray-100 ${isError ? "border-error" : "border-gray-500"}`

  return (
    <div className="flex min-h-screen flex-col bg-white text-gray-900">
      <main className="flex flex-1 flex-col lg:flex-row">
        <section className="flex items-center justify-center bg-marca p-12 lg:w-2/5">
          <div className="flex items-center gap-3">
            <Escudo className="size-7 text-gray-50" />
            <div className="flex flex-col gap-0.5">
              <span className="font-semibold text-gray-50">Sistema Logístico Policial</span>
              <span className="font-mono text-xs tracking-widest text-gray-400 uppercase">
                Dirección Logística
              </span>
            </div>
          </div>
        </section>

        <section className="flex flex-1 items-center justify-center px-6 py-12">
          <form onSubmit={handleSubmit} className="flex w-full max-w-sm flex-col gap-5">
            <h1 className="border-b border-gray-200 pb-4 text-2xl leading-tight font-semibold tracking-tight">
              Iniciar sesión
            </h1>

            {isError && (
              <div
                role="alert"
                className="flex items-center gap-2.5 rounded-xs border border-error px-4 py-3 text-sm font-medium text-error"
              >
                <svg
                  className="size-4 shrink-0"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  aria-hidden="true"
                >
                  <circle cx="12" cy="12" r="9" />
                  <path d="M12 8v5" />
                  <path d="M12 16h.01" />
                </svg>
                {error.message}
              </div>
            )}

            <div className="flex flex-col gap-1.5">
              <label htmlFor="usuario" className="text-sm font-semibold">
                Usuario
              </label>
              <input
                id="usuario"
                name="usuario"
                autoComplete="username"
                required
                disabled={isPending}
                aria-invalid={isError}
                className={claseInput}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="contrasena" className="text-sm font-semibold">
                Contraseña
              </label>
              <input
                id="contrasena"
                name="contrasena"
                type="password"
                autoComplete="current-password"
                required
                disabled={isPending}
                aria-invalid={isError}
                className={claseInput}
              />
            </div>

            <Boton type="submit" disabled={isPending} className="min-h-12">
              {isPending ? (
                <>
                  <svg
                    className="size-4 animate-spin"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    aria-hidden="true"
                  >
                    <path d="M21 12a9 9 0 1 1-9-9" />
                  </svg>
                  Verificando…
                </>
              ) : (
                "Ingresar"
              )}
            </Boton>
          </form>
        </section>
      </main>
    </div>
  )
}
