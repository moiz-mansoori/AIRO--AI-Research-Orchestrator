export interface Experiment {
  experiment_id: string
  task_type: 'classification' | 'regression'
  compute_budget: 'fast' | 'standard' | 'exhaustive'
  dataset_path: string
  status: 'running' | 'complete' | 'failed'
  created_at: string
}

export interface LeaderboardEntry {
  rank: number
  run_id: string
  model_type: string
  primary_metric: number
  secondary_metrics: Record<string, number>
  verdict: 'PASS' | 'WARN' | 'FAIL'
}

export interface CriticResult {
  run_id: string
  verdict: 'PASS' | 'WARN' | 'FAIL'
  issues: string[]
  recommendations: string[]
}

export interface AgentTiming {
  agent: string
  elapsed: number
  status: 'pending' | 'running' | 'done' | 'failed'
}

export interface ExperimentResult {
  experiment_id: string
  best_model_type: string
  best_run_id: string
  primary_metric_name: string
  improvement_over_baseline_pct: number
  leaderboard: LeaderboardEntry[]
  critic_results: CriticResult[]
  agent_timings: Record<string, number>
  report_md_path: string
  report_pdf_path: string
  errors: string[]
}
