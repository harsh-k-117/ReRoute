export type Location = { id: string; name: string; x?: number | null; y?: number | null };
export type Stop = {
  kind: string; delivery_id?: string | null; location_id: string; arrival: number;
  wait: number; service_start: number; depart: number; load_after: number;
  window_open?: number | null; window_close?: number | null; frozen?: boolean;
};
export type Route = { vehicle_id: string; stops: Stop[]; total_travel: number; total_wait: number; violations: string[] };
export type Unplaced = { delivery_id: string; reasons: { code: string; detail: string; vehicle_id?: string | null }[]; earliest_feasible_eta?: number | null };
export type Plan = { version_id: string; scenario_ref: string; routes: Route[]; unplaced: Unplaced[] };
export type Scenario = {
  name: string; depot_id: string; locations: Location[];
  vehicles: { id: string; name: string; capacity: number; start_location_id: string }[];
  deliveries: { id: string; location_id: string; demand: number; window_open: number; window_close: number; service_time: number }[];
  now: number; start_time: number;
};
export type ValidationReport = { passed: boolean; checks: { id: string; passed: boolean; details: string }[] };
export type UploadPreview = {
  token: string; format: string; counts: Record<string, number>;
  column_mapping: Record<string, string>; assumptions: string[];
  warnings: string[]; errors: string[];
};
export type UploadResult = { plan: Plan; validation_report: ValidationReport; scenario_name: string };
export type ImportPreview = {
  token: string; counts: Record<string, number>; missing_delivery_ids: string[];
  arrival_warnings: string[]; errors: string[];
};
export type ImportResult = {
  plan: Plan; validation_report: ValidationReport; is_valid: boolean;
  arrival_warnings: string[]; unplaced: string[];
};
export type DiffRow = {
  delivery_id: string; classification: "kept" | "moved" | "broken"; cause_code: string;
  sentence: string; before_vehicle_id?: string | null; after_vehicle_id?: string | null;
  before_eta?: number | null; after_eta?: number | null; badge?: string | null;
  earliest_feasible_eta?: number | null;
};
export type Diff = { rows: DiffRow[]; kept_count: number; moved_count: number; broken_count: number };
export type Disruption =
  | {
      type: "road_closure";
      a: string;
      b: string;
      mode: "add_minutes" | "set_minutes" | "multiply";
      value: number;
      both_directions?: boolean;
      start: number;
      end: number;
    }
  | { type: "vehicle_failure"; vehicle_id: string; at_time: number; transfer_minutes?: number | null }
  | { type: "urgent_delivery"; delivery: Scenario["deliveries"][number]; report_time: number; priority: number };
export type Proposal = {
  id: string; source: "form" | "text"; original_text?: string | null;
  disruption: Disruption; spans: { field: string; start: number; end: number }[];
  assumptions: string[]; warnings: string[]; rejections: string[]; status: "pending" | "confirmed" | "discarded";
  impact_preview?: { plan: Plan; diff: Diff; validation_report: ValidationReport } | null;
};
export type ReplanResult = { plan: Plan; previous_plan_ref: string; diff: Diff; validation_report: ValidationReport };

const baseUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init, headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);
  return response.json() as Promise<T>;
}

async function uploadRequest<T>(path: string, form: FormData): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, { method: "POST", body: form });
  if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);
  return response.json() as Promise<T>;
}

export const api = {
  scenarios: () => request<{ name: string }[]>("/scenarios"),
  scenario: (name: string) => request<Scenario>(`/scenarios/${encodeURIComponent(name)}`),
  initialPlan: (scenario: string) => request<{ plan: Plan; validation_report: ValidationReport }>("/plan/initial", {
    method: "POST", body: JSON.stringify({ scenario }),
  }),
  preview: (disruption: Record<string, unknown>) => request<Proposal>("/disruptions/preview", {
    method: "POST", body: JSON.stringify(disruption),
  }),
  interpret: (text: string) => request<Proposal>("/disruptions/interpret", {
    method: "POST", body: JSON.stringify({ text }),
  }),
  confirm: (id: string) => request<ReplanResult>(`/proposals/${encodeURIComponent(id)}/confirm`, { method: "POST" }),
  discard: (id: string) => request<Proposal>(`/proposals/${encodeURIComponent(id)}/discard`, { method: "POST" }),
  validate: (plan: Plan) => request<ValidationReport>("/validate", { method: "POST", body: JSON.stringify(plan) }),
  uploadScenarioPreview: (files: File[]) => {
    const form = new FormData();
    files.forEach((file, index) => form.append(index === 0 ? "file" : "files", file));
    return uploadRequest<UploadPreview>("/scenarios/upload/preview", form);
  },
  confirmScenarioUpload: (token: string) => request<UploadResult>("/scenarios/upload/confirm", {
    method: "POST", body: JSON.stringify({ token, build_plan_flag: true }),
  }),
  importPlanPreview: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return uploadRequest<ImportPreview>("/plan/import/preview", form);
  },
  confirmPlanImport: (token: string) => request<ImportResult>("/plan/import/confirm", {
    method: "POST", body: JSON.stringify({ token }),
  }),
};