import { Route, Routes } from "react-router-dom"
import { RutaProtegida } from "./componentes/RutaProtegida"
import { LayoutPrincipal } from "./layouts/LayoutPrincipal"
import { InventarioPagina } from "./paginas/InventarioPagina"
import { LoginPagina } from "./paginas/LoginPagina"
import { NoEncontradaPagina } from "./paginas/NoEncontradaPagina"
import { PorRecibirPagina } from "./paginas/PorRecibirPagina"
import { RevisionPagina } from "./paginas/RevisionPagina"

export const App = () => (
  <Routes>
    <Route path="/login" element={<LoginPagina />} />
    <Route element={<RutaProtegida />}>
      <Route element={<LayoutPrincipal />}>
        <Route index element={<InventarioPagina />} />
        <Route path="por-recibir" element={<PorRecibirPagina />} />
        <Route path="revision" element={<RevisionPagina />} />
        <Route path="*" element={<NoEncontradaPagina />} />
      </Route>
    </Route>
  </Routes>
)
