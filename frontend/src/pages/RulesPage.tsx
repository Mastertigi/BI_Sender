import { useEffect, useState } from "react";
import { api, RoutingRule, RoutingRuleInput } from "../api";
import RuleForm from "./RuleForm";

export default function RulesPage() {
  const [rules, setRules] = useState<RoutingRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [editing, setEditing] = useState<RoutingRule | null>(null);
  const [creating, setCreating] = useState(false);

  const load = () => {
    setLoading(true);
    api
      .listRules()
      .then(setRules)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const save = async (data: RoutingRuleInput) => {
    if (editing) await api.updateRule(editing.id, data);
    else await api.createRule(data);
    setEditing(null);
    setCreating(false);
    load();
  };

  const remove = async (r: RoutingRule) => {
    if (!confirm(`Excluir a regra "${r.diretoria} — ${r.report_display_name}"?`))
      return;
    await api.deleteRule(r.id);
    load();
  };

  return (
    <>
      <div className="toolbar">
        <h1 className="page-title" style={{ margin: 0 }}>
          Regras de Roteamento
        </h1>
        <button onClick={() => setCreating(true)}>+ Nova regra</button>
      </div>

      {err && <div className="error">{err}</div>}
      {loading ? (
        <div className="spinner">Carregando…</div>
      ) : (
        <div className="panel">
          <table>
            <thead>
              <tr>
                <th>Diretoria</th>
                <th>Relatório</th>
                <th>Página</th>
                <th>Destinatários</th>
                <th>RLS</th>
                <th>Entrega</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rules.map((r) => (
                <tr key={r.id}>
                  <td>{r.diretoria}</td>
                  <td>{r.report_display_name}</td>
                  <td className="muted">{r.page_name}</td>
                  <td>{r.email_to.join(", ") || "—"}</td>
                  <td className="muted">{r.rls_username || "—"}</td>
                  <td>{r.attach_pdf ? "Anexo PDF" : "Link"}</td>
                  <td>
                    <span
                      className={`badge ${r.active ? "SUCCEEDED" : "FAILED"}`}
                    >
                      {r.active ? "Ativa" : "Inativa"}
                    </span>
                  </td>
                  <td>
                    <div className="row">
                      <button
                        className="secondary"
                        onClick={() => setEditing(r)}
                      >
                        Editar
                      </button>
                      <button className="danger" onClick={() => remove(r)}>
                        Excluir
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {rules.length === 0 && (
                <tr>
                  <td colSpan={8} className="muted">
                    Nenhuma regra cadastrada.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {(creating || editing) && (
        <RuleForm
          initial={editing ?? undefined}
          onCancel={() => {
            setCreating(false);
            setEditing(null);
          }}
          onSave={save}
        />
      )}
    </>
  );
}
