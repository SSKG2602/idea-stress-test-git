const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_PREFIX = "/api/v1";
const POLL_INTERVAL_MS = 2000;
const MAX_POLL_ATTEMPTS = 90;
const DEVICE_ID_STORAGE_KEY = "device_id";

export type AnalysisStatus = "pending" | "running" | "complete" | "failed";

export interface ViabilityScore {
  raw_score: number;
  scaled_score: number;
  breakdown: Record<string, number>;
}

export interface MarketAnalysis {
  tam_estimate_range: string;
  market_growth_rate: string;
  saturation_score: number;
  trend_direction: "up" | "down" | "stable";
  confidence: number;
}

export interface Competitor {
  name: string;
  notable_strength: string;
}

export interface CompetitiveAnalysis {
  top_competitors: Competitor[];
  differentiation_strength: number;
  entry_barrier_score: number;
  red_flags: string[];
  moat_score: number;
}

export interface MonetizationAnalysis {
  willingness_to_pay_score: number;
  cac_risk_score: number;
  ltv_feasibility: number;
  monetization_difficulty: number;
}

export interface FailureSimulation {
  top_7_failure_modes: string[];
  highest_risk_area: string;
  survival_probability_downturn: number;
  survival_probability_regulation: number;
  survival_probability_competition: number;
}

export interface AuditResult {
  unsupported_claims: string[];
  uncertainty_flags: string[];
  overall_confidence_score: number;
}

export interface AnalysisResult {
  id: string;
  idea_text: string;
  status: AnalysisStatus;
  market: MarketAnalysis | null;
  competitive: CompetitiveAnalysis | null;
  monetization: MonetizationAnalysis | null;
  failure: FailureSimulation | null;
  audit: AuditResult | null;
  viability: ViabilityScore | null;
  search_snippets_used: number;
  created_at: string;
  completed_at: string | null;
  error: string | null;
}

interface AnalyzeResponse {
  analysis_id: string;
  status: AnalysisStatus;
  message: string;
}

interface TrackResponse {
  status: string;
}

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function createDeviceId(): string {
  if (typeof window !== "undefined" && window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `device-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function getOrCreateDeviceId(): string {
  if (typeof window === "undefined") {
    throw new Error("Device ID is only available in the browser.");
  }

  const existing = window.localStorage.getItem(DEVICE_ID_STORAGE_KEY);
  if (existing) {
    return existing;
  }

  const deviceId = createDeviceId();
  window.localStorage.setItem(DEVICE_ID_STORAGE_KEY, deviceId);
  return deviceId;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");

  if (typeof window !== "undefined") {
    headers.set("X-Device-Id", getOrCreateDeviceId());
  }

  const response = await fetch(`${API_BASE_URL}${API_PREFIX}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.text();
    let detailMessage: string | null = null;

    try {
      const parsed = JSON.parse(body) as { detail?: string };
      if (parsed.detail) {
        detailMessage = parsed.detail;
      }
    } catch {
      detailMessage = null;
    }

    if (detailMessage) {
      throw new Error(detailMessage);
    }

    throw new Error(body || `API ${response.status}: ${response.statusText}`);
  }

  return (await response.json()) as T;
}

export async function trackPageView(): Promise<void> {
  await apiFetch<TrackResponse>("/track", {
    method: "POST",
    body: JSON.stringify({ event_type: "page_view" }),
  });
}

export async function submitIdea(idea: string, tier: "free" | "paid" = "free"): Promise<string> {
  const payload = await apiFetch<AnalyzeResponse>("/analyze", {
    method: "POST",
    body: JSON.stringify({ idea, tier }),
  });
  return payload.analysis_id;
}

export async function getAnalysis(analysisId: string): Promise<AnalysisResult> {
  return apiFetch<AnalysisResult>(`/analysis/${analysisId}`);
}

export async function pollUntilDone(analysisId: string): Promise<AnalysisResult> {
  for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt += 1) {
    const result = await getAnalysis(analysisId);
    if (result.status === "complete" || result.status === "failed") {
      return result;
    }
    await wait(POLL_INTERVAL_MS);
  }

  throw new Error("Analysis timed out while polling for completion.");
}
