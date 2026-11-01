export type ModelOption = { id: string; label: string; reasoning: boolean };

export type Provider = {
  provider: string;
  label: string;
  has_key: boolean;
  key_env: string;
  models: ModelOption[];
};

export type Preset = {
  name: string;
  title: string;
  desc: string;
  code: string;
  notes: string;
  expect_clean: boolean;
};

export type Question = {
  id: number;
  topic: string;
  question: string;
  correct_answer: string;
  context: string;
  misconception_hint: string;
};

export type ModelResult = {
  label: string;
  provider: string;
  model: string;
  overall_accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  correct_only_accuracy: number;
  misconception_accuracy: number;
  tp: number;
  fp: number;
  fn: number;
  tn: number;
};

export type Misconception = {
  id: number;
  description: string;
  example: string;
  constructs: string[];
};

export type Candidate = { id: number; description: string; constructs: string[] };

export type Diagnosis = {
  trace: string;
  verification: string;
  misconception_found: boolean;
  description: string;
  explanation: string;
  raw_response: string;
  parse_success: boolean;
  retrieved_candidates: Candidate[];
};

export class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError("Can't reach the MisconAI API. Start it with: python src/server.py");
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      if (res.status >= 500) detail = "The MisconAI API is not responding. Start it with: python src/server.py";
    }
    throw new ApiError(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  models: () => request<Provider[]>("/models"),
  presets: () => request<Preset[]>("/presets"),
  questions: () => request<Question[]>("/questions"),
  results: () => request<ModelResult[]>("/results"),
  taxonomy: () => request<Misconception[]>("/taxonomy"),
  analyzeCode: (body: { provider: string; model: string; title: string; description: string; code: string }) =>
    request<Diagnosis>("/analyze/code", { method: "POST", body: JSON.stringify(body) }),
  analyzeAnswer: (body: { provider: string; model: string; question_id: number; answer: string }) =>
    request<Diagnosis>("/analyze/answer", { method: "POST", body: JSON.stringify(body) }),
};

export const pct = (v: number) => `${(v * 100).toFixed(1)}%`;
export const humanize = (s: string) => s.replace(/_/g, " ");
