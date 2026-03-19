from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

# Enums
class TaskType(StrEnum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"

class ComputeBudget(StrEnum):
    FAST = "fast"           # 3 configs
    STANDARD = "standard"  # 6 configs
    EXHAUSTIVE = "exhaustive"  # 10 configs

class CriticVerdict(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"

class PipelineAction(StrEnum):
    CONTINUE = "CONTINUE"
    REGENERATE_CONFIGS = "REGENERATE_CONFIGS"
    STOP = "STOP"

# Sub-models    
@dataclass
class DataQualityReport:
    row_count: int = 0
    feature_count: int = 0
    null_pct: dict[str, float] = field(default_factory=dict)
    duplicate_rows: int = 0
    class_distribution: dict[str, int] = field(default_factory=dict)  # classification only
    imbalance_ratio: float | None = None
    warnings: list[str] = field(default_factory=list)

@dataclass
class ExperimentConfig:
    config_id: str = ""
    model_type: str = ""
    hyperparams: dict[str, Any] = field(default_factory=dict)
    feature_subset: list[str] | str = "all"
    random_seed: int = 42
    notes: str = ""

@dataclass
class TrainingResult:
    run_id: str = ""
    config_id: str = ""
    model_type: str = ""
    status: str = "PENDING"      # PENDING | COMPLETED | FAILED
    train_metrics: dict[str, float] = field(default_factory=dict)
    val_metrics: dict[str, float] = field(default_factory=dict)
    training_time_s: float = 0.0
    model_artifact_path: str = ""
    error_message: str | None = None

@dataclass
class CriticResult:
    run_id: str = ""
    verdict: CriticVerdict = CriticVerdict.FAIL
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

@dataclass
class LeaderboardEntry:
    rank: int = 0
    run_id: str = ""
    model_type: str = ""
    primary_metric: float = 0.0
    secondary_metrics: dict[str, float] = field(default_factory=dict)
    verdict: CriticVerdict = CriticVerdict.PASS

# Main State 
@dataclass
class AIROState:
    """
    Single source of truth across all AIRO pipeline agents.
    LangGraph passes this object between every node.
    """
    # Identity 
    experiment_id: str = field(default_factory=lambda: f"airo_{uuid.uuid4().hex[:8]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # User inputs 
    dataset_path: str = ""
    task_type: TaskType = TaskType.CLASSIFICATION
    compute_budget: ComputeBudget = ComputeBudget.STANDARD
    target_column: str = ""

    # Data Agent outputs 
    artifact_path: str = ""
    feature_schema: dict[str, str] = field(default_factory=dict)   # col → dtype
    quality_report: DataQualityReport = field(default_factory=DataQualityReport)
    split_sizes: dict[str, int] = field(default_factory=dict)       # train/val/test counts

    # Config Agent outputs 
    configs: list[ExperimentConfig] = field(default_factory=list)

    # Training Agent outputs 
    training_results: list[TrainingResult] = field(default_factory=list)

    # Critic Agent outputs 
    critic_results: list[CriticResult] = field(default_factory=list)
    pipeline_action: PipelineAction = PipelineAction.CONTINUE

    # Evaluator Agent outputs 
    leaderboard: list[LeaderboardEntry] = field(default_factory=list)
    best_run_id: str = ""
    best_model_type: str = ""
    improvement_over_baseline_pct: float = 0.0
    selection_reasoning: str = ""

    # Reporter Agent outputs 
    report_md_path: str = ""
    report_pdf_path: str = ""
    leaderboard_csv_path: str = ""

    # Pipeline meta 
    current_agent: str = ""
    errors: list[str] = field(default_factory=list)
    retry_count: int = 0
    agent_timings: dict[str, float] = field(default_factory=dict)  # agent → seconds

    # Convenience helpers 
    def passed_runs(self) -> list[TrainingResult]:
        """Return training results that passed or warned the critic."""
        valid_ids = {
            r.run_id for r in self.critic_results
            if r.verdict in (CriticVerdict.PASS, CriticVerdict.WARN)
        }
        return [t for t in self.training_results if t.run_id in valid_ids]

    def failed_runs(self) -> list[TrainingResult]:
        """Return training results that failed the critic."""
        fail_ids = {
            r.run_id for r in self.critic_results
            if r.verdict == CriticVerdict.FAIL
        }
        return [t for t in self.training_results if t.run_id in fail_ids]

    def primary_metric_name(self) -> str:
        return "f1_macro" if self.task_type == TaskType.CLASSIFICATION else "rmse"

    def add_error(self, agent: str, message: str) -> None:
        self.errors.append(f"[{agent}] {message}")

    def log_timing(self, agent: str, elapsed: float) -> None:
        self.agent_timings[agent] = round(elapsed, 2)
