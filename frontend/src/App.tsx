import { lazy, Suspense } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";

// Code-splitting por rota: cada página vira um chunk carregado sob demanda.
const Dashboard = lazy(() => import("./pages/Dashboard"));
const RulesPage = lazy(() => import("./pages/RulesPage"));
const ExecutionsPage = lazy(() => import("./pages/ExecutionsPage"));

export default function App() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          BI <span>Notify</span>
        </div>
        <NavLink to="/dashboard" className="nav-link">
          Dashboard
        </NavLink>
        <NavLink to="/rules" className="nav-link">
          Regras de Roteamento
        </NavLink>
        <NavLink to="/executions" className="nav-link">
          Execuções
        </NavLink>
      </aside>
      <main className="content">
        <Suspense fallback={<div className="spinner">Carregando…</div>}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/rules" element={<RulesPage />} />
            <Route path="/executions" element={<ExecutionsPage />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}
