// Cliente de API tipado para o backend BI Notify.
const BASE = import.meta.env.VITE_API_BASE ?? "/api";

// ── Tipos ──────────────────────────────────────────────
export interface RoutingRule {
  id: number;
  diretoria: string;
  workspace_id: string;
  dataset_id: string;
  report_id: string;
  page_name: string;
  report_display_name: string;
  rls_username?: string | null;
  rls_roles?: string[] | null;
  report_level_filters?: string | null;
  email_to: string[];
  email_cc?: string[] | null;
  teams_team_id?: string | null;
  teams_channel_id?: string | null;
  attach_pdf: boolean;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export type RoutingRuleInput = Omit<
  RoutingRule,
  "id" | "created_at" | "updated_at"
>;

export interface Execution {
  id: number;
  correlation_id: string;
  status: string;
  diretoria?: string | null;
  workspace_id?: string | null;
  dataset_id?: string | null;
  report_id?: string | null;
  page_name?: string | null;
  powerbi_export_id?: string | null;
  error_detail?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExecutionPage {
  total: number;
  items: Execution[];
}

export interface DashboardMetrics {
  total: number;
  succeeded: number;
  failed: number;
  in_progress: number;
  success_rate: number;
  by_status: { status: string; count: number }[];
  by_diretoria: { diretoria: string; count: number }[];
}

// ── HTTP helper ────────────────────────────────────────
async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// ── Regras de roteamento ───────────────────────────────
export const api = {
  listRules: (params?: { active?: boolean; diretoria?: string }) => {
    const q = new URLSearchParams();
    if (params?.active !== undefined) q.set("active", String(params.active));
    if (params?.diretoria) q.set("diretoria", params.diretoria);
    const qs = q.toString();
    return http<RoutingRule[]>(`/routing-rules${qs ? `?${qs}` : ""}`);
  },
  createRule: (data: RoutingRuleInput) =>
    http<RoutingRule>("/routing-rules", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateRule: (id: number, data: Partial<RoutingRuleInput>) =>
    http<RoutingRule>(`/routing-rules/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteRule: (id: number) =>
    http<void>(`/routing-rules/${id}`, { method: "DELETE" }),

  // ── Execuções ──
  listExecutions: (params?: { status?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    const qs = q.toString();
    return http<ExecutionPage>(`/executions${qs ? `?${qs}` : ""}`);
  },
  metrics: () => http<DashboardMetrics>("/executions/metrics"),
  trigger: (workspace_id: string, dataset_id: string) =>
    http<{ correlation_id: string; task_id: string }>("/executions/trigger", {
      method: "POST",
      body: JSON.stringify({ workspace_id, dataset_id }),
    }),
};

export const STATUS_LABEL: Record<string, string> = {
  PENDING: "Pendente",
  REFRESHING_DATASET: "Atualizando dataset",
  EXPORTING: "Exportando",
  DELIVERING: "Entregando",
  SUCCEEDED: "Concluído",
  FAILED: "Falhou",
};
