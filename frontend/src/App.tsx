import { lazy, Suspense } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const RulesPage = lazy(() => import("./pages/RulesPage"));
const ExecutionsPage = lazy(() => import("./pages/ExecutionsPage"));
const Docs = lazy(() => import("./pages/Docs"));

const IconHome = () => (
  <svg viewBox="0 0 24 24" fill="none"><path d="M3 10.5 12 3l9 7.5M5 9.5V20a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
);
const IconRules = () => (
  <svg viewBox="0 0 24 24" fill="none"><path d="M4 6h16M4 12h16M4 18h10" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /><circle cx="18" cy="18" r="2.5" stroke="currentColor" strokeWidth="1.8" /></svg>
);
const IconRuns = () => (
  <svg viewBox="0 0 24 24" fill="none"><path d="M12 7v5l3 2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /><circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.8" /></svg>
);
const IconDocs = () => (
  <svg viewBox="0 0 24 24" fill="none"><path d="M7 3h7l5 5v13a0 0 0 0 1 0 0H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" /><path d="M14 3v5h5M8.5 13h7M8.5 17h7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" /></svg>
);

export default function App() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <span className="logo">BI</span>
          <span>
            BI <span className="grad-text">Notify</span>
          </span>
        </div>
        <div className="brand-tag">Entrega automatizada de relatórios Power BI</div>

        <NavLink to="/dashboard" className="nav-link">
          <IconHome /> Dashboard
        </NavLink>
        <NavLink to="/rules" className="nav-link">
          <IconRules /> Regras de Roteamento
        </NavLink>
        <NavLink to="/executions" className="nav-link">
          <IconRuns /> Execuções
        </NavLink>
        <NavLink to="/docs" className="nav-link">
          <IconDocs /> Documentação
        </NavLink>

        <div className="sidebar-foot">v1.1 · FastAPI · Celery · Graph</div>
      </aside>
      <main className="content">
        <Suspense fallback={<div className="spinner">Carregando…</div>}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/rules" element={<RulesPage />} />
            <Route path="/executions" element={<ExecutionsPage />} />
            <Route path="/docs" element={<Docs />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}
