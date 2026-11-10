import { Route, Routes } from "react-router-dom"
import { RutaProtegida } from "./componentes/RutaProtegida"
import { LayoutPrincipal } from "./layouts/LayoutPrincipal"
import { DevueltasPagina } from "./paginas/DevueltasPagina"
import { HistorialBienPagina } from "./paginas/HistorialBienPagina"
import { InicioPagina } from "./paginas/InicioPagina"
import { InventarioPagina } from "./paginas/InventarioPagina"
import { LoginPagina } from "./paginas/LoginPagina"
import { NoEncontradaPagina } from "./paginas/NoEncontradaPagina"
import { ObservadosPagina } from "./paginas/ObservadosPagina"
import { PorRecibirPagina } from "./paginas/PorRecibirPagina"
import { RevisionPagina } from "./paginas/RevisionPagina"

export const App = () => (
  <Routes>
    <Route path="/login" element={<LoginPagina />} />
    <Route element={<RutaProtegida />}>
      <Route element={<LayoutPrincipal />}>
        <Route index element={<InicioPagina />} />
        <Route path="inventario" element={<InventarioPagina />} />
        <Route path="bienes/:id" element={<HistorialBienPagina />} />
        <Route path="por-recibir" element={<PorRecibirPagina />} />
        <Route path="devueltas" element={<DevueltasPagina />} />
        <Route path="observados" element={<ObservadosPagina />} />
        <Route path="revision" element={<RevisionPagina />} />
        <Route path="*" element={<NoEncontradaPagina />} />
      </Route>
    </Route>
  </Routes>
)
