// API client for backend integration

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ExperimentConfig {
  market_slug: string;
  start_time: string; // ISO datetime
  end_time: string; // ISO datetime
  interval_minutes: number;
  num_simulations: number;
  model_provider: string;
  mode: 'daytona_agent' | 'direct_llm';
}

export interface MarketMetadata {
  title: string;
  description: string;
  markets?: Array<{
    question: string;
    active: boolean;
    closed: boolean;
    endDateIso: string;
    clobTokenIds: string | string[];
  }>;
}

export interface AgentDecision {
  decision: 'YES' | 'NO';
  confidence: number;
  rationale: string;
  relevant_evidence_ids: string[];
  execution_trace?: {
    code: string;
    raw_output: string;
    exit_code: number;
    executed_successfully: boolean;
    execution_time_ms?: number;
    error_message?: string;
    attempt_number: number;
  };
}

export interface IntervalResult {
  timestamp: string;
  market_state: {
    timestamp: string;
    price: number;
    volume?: number;
  };
  decisions: AgentDecision[];
  aggregated_decision: 'YES' | 'NO';
  aggregated_confidence: number;
}

export interface ExperimentResult {
  id: string;
  config: ExperimentConfig;
  timeline: IntervalResult[];
  created_at: string;
}

export async function fetchMarketMetadata(slug: string): Promise<MarketMetadata> {
  const response = await fetch(`${API_BASE_URL}/api/markets/${slug}/metadata`);
  if (!response.ok) {
    throw new Error(`Failed to fetch market metadata: ${response.statusText}`);
  }
  return response.json();
}

export async function runExperiment(config: ExperimentConfig): Promise<{ experiment_id: string }> {
  const response = await fetch(`${API_BASE_URL}/api/experiments/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error || `Failed to run experiment: ${response.statusText}`);
  }
  
  return response.json();
}

export async function getExperiment(experimentId: string): Promise<ExperimentResult> {
  const response = await fetch(`${API_BASE_URL}/api/experiments/${experimentId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch experiment: ${response.statusText}`);
  }
  return response.json();
}

export async function listExperiments(): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/api/experiments`);
  if (!response.ok) {
    throw new Error(`Failed to list experiments: ${response.statusText}`);
  }
  return response.json();
}

export interface ExperimentProgress {
  experiment_id: string;
  total_intervals: number;
  completed_intervals: number;
  failed_intervals: number;
  progress_percent: number;
  status: 'running' | 'completed' | 'failed';
  elapsed_seconds: number;
  error?: string | null;
}

export async function getExperimentProgress(experimentId: string): Promise<ExperimentProgress> {
  const response = await fetch(`${API_BASE_URL}/api/experiments/${experimentId}/progress`);
  if (!response.ok) {
    throw new Error(`Failed to fetch experiment progress: ${response.statusText}`);
  }
  return response.json();
}

