import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, DashboardMetrics, STATUS_LABEL } from "../api";
import { Hero, Pipeline } from "../components/Pipeline";

const STATUS_COLORS: Record<string, string> = {
  SUCCEEDED: "#38e08a",
  FAILED: "#ff5d6c",
  PENDING: "#2bd4ff",
  REFRESHING_DATASET: "#2bd4ff",
  EXPORTING: "#2bd4ff",
  DELIVERING: "#f5c451",
};

const tooltipStyle = {
  background: "#121a30",
  border: "1px solid rgba(80,110,170,0.3)",
  borderRadius: 10,
  color: "#eaf0fb",
};

export default function Dashboard() {
  const [m, setM] = useState<DashboardMetrics | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = () => api.metrics().then(setM).catch((e) => setErr(String(e)));

  useEffect(() => {
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, []);

  const pie =
    m?.by_status.map((s) => ({
      name: STATUS_LABEL[s.status] ?? s.status,
      value: s.count,
      key: s.status,
    })) ?? [];

  return (
    <>
      <Hero />
      <Pipeline />

      <div className="pipeline-head">
        <h3>Visão geral</h3>
        <span>atualiza a cada 15s</span>
      </div>

      {err && <div className="error">Erro ao carregar métricas: {err}</div>}
      {!m ? (
        <div className="spinner">Carregando métricas…</div>
      ) : (
        <>
          <div className="cards">
            <div className="card">
              <div className="label">Execuções (total)</div>
              <div className="value cyan">{m.total}</div>
            </div>
            <div className="card">
              <div className="label">Concluídas</div>
              <div className="value ok">{m.succeeded}</div>
            </div>
            <div className="card">
              <div className="label">Falhas</div>
              <div className="value fail">{m.failed}</div>
            </div>
            <div className="card">
              <div className="label">Taxa de sucesso</div>
              <div className="value warn">{m.success_rate}%</div>
            </div>
          </div>

          <div className="panel">
            <h3>Execuções por status</h3>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={pie} dataKey="value" nameKey="name" outerRadius={100} label>
                  {pie.map((d) => (
                    <Cell key={d.key} fill={STATUS_COLORS[d.key] ?? "#8b97b5"} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="panel">
            <h3>Execuções por diretoria</h3>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={m.by_diretoria}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(80,110,170,0.2)" />
                <XAxis dataKey="diretoria" stroke="#8b97b5" />
                <YAxis stroke="#8b97b5" allowDecimals={false} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(43,212,255,0.06)" }} />
                <Bar dataKey="count" fill="#2bd4ff" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </>
  );
}
