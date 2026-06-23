import { useEffect, useState } from "react";
import { api, Execution, STATUS_LABEL } from "../api";

const STATUSES = [
  "",
  "PENDING",
  "REFRESHING_DATASET",
  "EXPORTING",
  "DELIVERING",
  "SUCCEEDED",
  "FAILED",
];

function TriggerBox({ onDone }: { onDone: () => void }) {
  const [ws, setWs] = useState("");
  const [ds, setDs] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const run = async () => {
    setBusy(true);
    setMsg(null);
    try {
      const r = await api.trigger(ws, ds);
      setMsg(`Disparado! correlation_id=${r.correlation_id}`);
      onDone();
    } catch (e) {
      setMsg(`Erro: ${e}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="panel">
      <h3>Disparo manual do pipeline</h3>
      <div className="row">
        <input
          placeholder="Workspace ID"
          value={ws}
          onChange={(e) => setWs(e.target.value)}
          style={{ maxWidth: 280 }}
        />
        <input
          placeholder="Dataset ID"
          value={ds}
          onChange={(e) => setDs(e.target.value)}
          style={{ maxWidth: 280 }}
        />
        <button onClick={run} disabled={busy || !ws || !ds}>
          {busy ? "Disparando…" : "Disparar"}
        </button>
      </div>
      {msg && <div className="muted" style={{ marginTop: 10 }}>{msg}</div>}
    </div>
  );
}

export default function ExecutionsPage() {
  const [items, setItems] = useState<Execution[]>([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const load = () =>
    api
      .listExecutions({ status: status || undefined, limit: 100 })
      .then((p) => {
        setItems(p.items);
        setTotal(p.total);
      })
      .catch((e) => setErr(String(e)));

  useEffect(() => {
    load();
    const t = setInterval(load, 8000); // auto-refresh do monitor
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  return (
    <>
      <h1 className="page-title">Execuções</h1>
      <TriggerBox onDone={load} />

      <div className="toolbar">
        <div className="row">
          <span className="muted">Filtrar status:</span>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            style={{ width: 220 }}
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s ? STATUS_LABEL[s] ?? s : "Todos"}
              </option>
            ))}
          </select>
        </div>
        <span className="muted">{total} registro(s)</span>
      </div>

      {err && <div className="error">{err}</div>}
      <div className="panel">
        <table>
          <thead>
            <tr>
              <th>Correlation</th>
              <th>Diretoria</th>
              <th>Relatório / Página</th>
              <th>Status</th>
              <th>Atualizado</th>
              <th>Erro</th>
            </tr>
          </thead>
          <tbody>
            {items.map((e) => (
              <tr key={e.id}>
                <td className="muted">{e.correlation_id.slice(0, 10)}…</td>
                <td>{e.diretoria ?? "—"}</td>
                <td>
                  {e.report_id ? `${e.report_id.slice(0, 8)}…` : "—"}
                  {e.page_name ? ` / ${e.page_name}` : ""}
                </td>
                <td>
                  <span className={`badge ${e.status}`}>
                    {STATUS_LABEL[e.status] ?? e.status}
                  </span>
                </td>
                <td className="muted">
                  {new Date(e.updated_at).toLocaleString("pt-BR")}
                </td>
                <td className="muted" style={{ maxWidth: 260 }}>
                  {e.error_detail ?? ""}
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={6} className="muted">
                  Nenhuma execução.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
