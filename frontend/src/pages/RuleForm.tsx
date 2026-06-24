import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
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
const parseCsv = (s: string) => s.split(",").map((x) => x.trim()).filter(Boolean);

// Onde achar cada item — instrução curta exibida abaixo do campo.
const HINTS: Record<string, string> = {
  diretoria: "Nome livre da área (ex.: Financeiro). Serve só para organizar o roteamento.",
  report_display_name: "Nome que aparece no PDF, no assunto do e-mail e na mensagem do Teams.",
  workspace_id:
    "Power BI Service → abra o workspace. Na URL: app.powerbi.com/groups/{ESTE-ID}/list",
  dataset_id:
    "Workspace → reticências (…) do modelo semântico → Configurações. Na URL: …/datasets/{ESTE-ID}",
  report_id:
    "Abra o relatório no Service. Na URL: …/reports/{ESTE-ID}/ReportSection…",
  page_name:
    "É o trecho 'ReportSection…' no fim da URL ao abrir a página desejada (ou via API Get Pages).",
  email_to: "E-mails dos destinatários separados por vírgula.",
  email_cc: "Opcional — destinatários em cópia (vírgula).",
  rls_username:
    "UPN/e-mail usado como identidade efetiva no RLS (ex.: financeiro@empresa.com.br).",
  rls_roles:
    "Nomes EXATOS das funções criadas em 'Gerenciar funções' do dataset (vírgula).",
  teams_team_id:
    "Teams → (…) do time → 'Obter link para a equipe' → copie o valor de groupId=.",
  teams_channel_id:
    "Teams → (…) do canal → 'Obter link para o canal' → copie o id no formato 19:…@thread.tacv2.",
  report_level_filters:
    "Opcional. Sintaxe de filtro: Tabela/Campo eq 'valor' (sem o ?filter= da URL).",
};

export default function RuleForm({ initial, onCancel, onSave }: Props) {
  const [f, setF] = useState<RoutingRuleInput>(initial ? { ...initial } : { ...empty });
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

  const field = (key: keyof RoutingRuleInput, label: string, placeholder = "") => (
    <label className="field">
      <span>{label}</span>
      <input
        value={(f[key] as string) ?? ""}
        placeholder={placeholder}
        onChange={(e) => set(key, e.target.value as never)}
      />
      {HINTS[key as string] && <small className="hint">{HINTS[key as string]}</small>}
    </label>
  );

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>{initial ? "Editar regra" : "Nova regra de roteamento"}</h2>

        <div className="callout">
          <strong>Como preencher:</strong> cada campo abaixo traz onde encontrar o
          valor. Para o passo a passo completo (Service Principal, permissões e
          captura dos IDs), veja a{" "}
          <Link to="/docs" onClick={onCancel}>página de Documentação</Link>.
        </div>

        <form onSubmit={submit}>
          <p className="form-section">1 · Identificação</p>
          <div className="grid-2">
            {field("diretoria", "Diretoria *", "Financeiro")}
            {field("report_display_name", "Nome do relatório *", "Financeiro")}
          </div>

          <p className="form-section">2 · Origem no Power BI</p>
          <div className="grid-2">
            {field("workspace_id", "Workspace ID *")}
            {field("dataset_id", "Dataset ID *")}
            {field("report_id", "Report ID *")}
            {field("page_name", "Página (pageName) *", "ReportSection0a1b…")}
          </div>

          <p className="form-section">3 · Segurança por linha (RLS) — opcional</p>
          <div className="grid-2">
            {field("rls_username", "RLS username (effectiveIdentity)")}
            <label className="field">
              <span>RLS roles (vírgula)</span>
              <input value={roles} onChange={(e) => setRoles(e.target.value)} />
              <small className="hint">{HINTS.rls_roles}</small>
            </label>
          </div>
          {field("report_level_filters", "Filtro de relatório (URL filter)")}

          <p className="form-section">4 · Entrega</p>
          <label className="field">
            <span>Destinatários de e-mail (vírgula) *</span>
            <input
              value={emailTo}
              placeholder="diretor@empresa.com, gestor@empresa.com"
              onChange={(e) => setEmailTo(e.target.value)}
            />
            <small className="hint">{HINTS.email_to}</small>
          </label>
          <label className="field">
            <span>E-mail em cópia (CC)</span>
            <input value={emailCc} onChange={(e) => setEmailCc(e.target.value)} />
            <small className="hint">{HINTS.email_cc}</small>
          </label>
          <div className="grid-2">
            {field("teams_team_id", "Teams Team ID")}
            {field("teams_channel_id", "Teams Channel ID")}
          </div>

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
