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

const STATUS_COLORS: Record<string, string> = {
  SUCCEEDED: "#38e08a",
  FAILED: "#ff5d6c",
  PENDING: "#2bd4ff",
  REFRESHING_DATASET: "#2bd4ff",
  EXPORTING: "#2bd4ff",
  DELIVERING: "#f5c451",
};

export default function Dashboard() {
  const [m, setM] = useState<DashboardMetrics | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = () =>
    api.metrics().then(setM).catch((e) => setErr(String(e)));

  useEffect(() => {
    load();
    const t = setInterval(load, 15000); // auto-refresh
    return () => clearInterval(t);
  }, []);

  if (err) return <div className="error">Erro ao carregar métricas: {err}</div>;
  if (!m) return <div className="spinner">Carregando…</div>;

  const pie = m.by_status.map((s) => ({
    name: STATUS_LABEL[s.status] ?? s.status,
    value: s.count,
    key: s.status,
  }));

  return (
    <>
      <h1 className="page-title">Dashboard</h1>
      <div className="cards">
        <div className="card">
          <div className="label">Total de execuções</div>
          <div className="value">{m.total}</div>
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
                <Cell key={d.key} fill={STATUS_COLORS[d.key] ?? "#8a93ad"} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="panel">
        <h3>Execuções por diretoria</h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={m.by_diretoria}>
            <CartesianGrid strokeDasharray="3 3" stroke="#273150" />
            <XAxis dataKey="diretoria" stroke="#8a93ad" />
            <YAxis stroke="#8a93ad" allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="count" fill="#2bd4ff" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}
