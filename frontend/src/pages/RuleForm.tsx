import { FormEvent, useState } from "react";
import { RoutingRule, RoutingRuleInput } from "../api";

interface Props {
  initial?: RoutingRule;
  onCancel: () => void;
  onSave: (data: RoutingRuleInput) => Promise<void>;
}

const empty: RoutingRuleInput = {
  diretoria: "",
  workspace_id: "",
  dataset_id: "",
  report_id: "",
  page_name: "",
  report_display_name: "",
  rls_username: "",
  rls_roles: [],
  report_level_filters: "",
  email_to: [],
  email_cc: [],
  teams_team_id: "",
  teams_channel_id: "",
  attach_pdf: true,
  active: true,
};

const csv = (v?: string[] | null) => (v ?? []).join(", ");
const parseCsv = (s: string) =>
  s.split(",").map((x) => x.trim()).filter(Boolean);

export default function RuleForm({ initial, onCancel, onSave }: Props) {
  const [f, setF] = useState<RoutingRuleInput>(
    initial ? { ...initial } : { ...empty }
  );
  const [emailTo, setEmailTo] = useState(csv(initial?.email_to));
  const [emailCc, setEmailCc] = useState(csv(initial?.email_cc));
  const [roles, setRoles] = useState(csv(initial?.rls_roles));
  const [err, setErr] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const set = <K extends keyof RoutingRuleInput>(k: K, v: RoutingRuleInput[K]) =>
    setF((p) => ({ ...p, [k]: v }));

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setErr(null);
    setSaving(true);
    try {
      await onSave({
        ...f,
        email_to: parseCsv(emailTo),
        email_cc: parseCsv(emailCc),
        rls_roles: parseCsv(roles),
      });
    } catch (e2) {
      setErr(String(e2));
    } finally {
      setSaving(false);
    }
  };

  const field = (
    key: keyof RoutingRuleInput,
    label: string,
    placeholder = ""
  ) => (
    <label className="field">
      <span>{label}</span>
      <input
        value={(f[key] as string) ?? ""}
        placeholder={placeholder}
        onChange={(e) => set(key, e.target.value as never)}
      />
    </label>
  );

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>{initial ? "Editar regra" : "Nova regra de roteamento"}</h2>
        <form onSubmit={submit}>
          <div className="grid-2">
            {field("diretoria", "Diretoria *", "Financeiro")}
            {field("report_display_name", "Nome do relatório *", "Financeiro")}
            {field("workspace_id", "Workspace ID *")}
            {field("dataset_id", "Dataset ID *")}
            {field("report_id", "Report ID *")}
            {field("page_name", "Página (pageName) *", "ReportSection...")}
          </div>

          <label className="field">
            <span>Destinatários e-mail (separados por vírgula) *</span>
            <input
              value={emailTo}
              placeholder="diretor@empresa.com, gestor@empresa.com"
              onChange={(e) => setEmailTo(e.target.value)}
            />
          </label>
          <label className="field">
            <span>E-mail em cópia (CC)</span>
            <input value={emailCc} onChange={(e) => setEmailCc(e.target.value)} />
          </label>

          <div className="grid-2">
            {field("rls_username", "RLS username (effectiveIdentity)")}
            <label className="field">
              <span>RLS roles (vírgula)</span>
              <input value={roles} onChange={(e) => setRoles(e.target.value)} />
            </label>
            {field("teams_team_id", "Teams Team ID")}
            {field("teams_channel_id", "Teams Channel ID")}
          </div>
          {field("report_level_filters", "Filtro de relatório (URL filter)")}

          <div className="row" style={{ margin: "10px 0 18px" }}>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={f.attach_pdf}
                onChange={(e) => set("attach_pdf", e.target.checked)}
              />
              Anexar PDF (senão, enviar link)
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={f.active}
                onChange={(e) => set("active", e.target.checked)}
              />
              Ativa
            </label>
          </div>

          {err && <div className="error">{err}</div>}
          <div className="row" style={{ justifyContent: "flex-end" }}>
            <button type="button" className="secondary" onClick={onCancel}>
              Cancelar
            </button>
            <button type="submit" disabled={saving}>
              {saving ? "Salvando…" : "Salvar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
