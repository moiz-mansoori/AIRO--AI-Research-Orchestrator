"""
AIRO — agents/critic_agent.py
Audits every trained model for validity before it reaches the evaluator.
"""
from __future__ import annotations
import time
from orchestrator.state import (
    AIROState, CriticResult, CriticVerdict, PipelineAction, TaskType
)

# Thresholds — tune per project needs
OVERFIT_THRESHOLD    = 0.15   # train - val gap
LEAKAGE_THRESHOLD    = 0.05   # val - train gap (val suspiciously better)
MIN_TEST_SAMPLES     = 100


def _audit_run(run_id: str, state: AIROState) -> CriticResult:
    """
    Audit a single training run.

    Checks (in order):
      1. Training failure      → FAIL
      2. Data leakage          → FAIL  (val >> train)
      3. Overfitting           → WARN  (train >> val)
      4. Small test set        → WARN
      5. Worse than baseline   → WARN

    Returns CriticResult with verdict + actionable recommendations.
    """
    result = CriticResult(run_id=run_id, verdict=CriticVerdict.PASS)
    training = next((t for t in state.training_results if t.run_id == run_id), None)

    if training is None or training.status == "FAILED":
        result.verdict = CriticVerdict.FAIL
        result.issues = [f"Training failed: {training.error_message if training else 'unknown'}"]
        result.recommendations = []
        return result

    metric = state.primary_metric_name()
    train_m = training.train_metrics.get(metric, 0.0)
    val_m   = training.val_metrics.get(metric, 0.0)
    test_n  = state.split_sizes.get("test", 0)

    issues, recs = [], []

    if val_m - train_m > LEAKAGE_THRESHOLD:
        issues.append(f"Possible data leakage: val {metric}={val_m:.3f} >> train {metric}={train_m:.3f}")
        recs.append("Audit preprocessing pipeline for target leakage — check fit_transform vs transform usage.")
        result.verdict = CriticVerdict.FAIL
    if train_m - val_m > OVERFIT_THRESHOLD:
        issues.append(f"Overfitting detected: train-val gap = {train_m - val_m:.3f}")
        recs.append("Increase regularization, add dropout (for MLP), or reduce model complexity.")
        if result.verdict != CriticVerdict.FAIL:
            result.verdict = CriticVerdict.WARN

    if test_n < MIN_TEST_SAMPLES:
        issues.append(f"Test set too small ({test_n} samples) — metrics may be unreliable.")
        recs.append("Collect more data or use cross-validation instead of a held-out split.")
        if result.verdict not in (CriticVerdict.FAIL, CriticVerdict.WARN):
            result.verdict = CriticVerdict.WARN

    baseline = next(
        (t for t in state.training_results if t.config_id.endswith("_0") or "baseline" in t.config_id),
        None,
    )
    if baseline and val_m < baseline.val_metrics.get(metric, 0.0) - 0.01:
        issues.append(f"Model performs worse than baseline ({val_m:.3f} vs {baseline.val_metrics.get(metric, 0):.3f})")
        recs.append("Review feature subset or hyperparameter choices — baseline outperforms this config.")
        if result.verdict not in (CriticVerdict.FAIL,):
            result.verdict = CriticVerdict.WARN


    result.issues = list(issues)
    result.recommendations = list(recs)
    return result


def critic_agent_node(state: AIROState) -> AIROState:
    """
    LangGraph node: Critic Agent.

    Audits all training results. If every run fails, sets
    pipeline_action = REGENERATE_CONFIGS so the router retries.

    Returns updated AIROState.
    """
    t0 = time.perf_counter()
    state.current_agent = "critic"

    state.critic_results = [
        _audit_run(t.run_id, state) for t in state.training_results
    ]

    all_failed = all(r.verdict == CriticVerdict.FAIL for r in state.critic_results)
    state.pipeline_action = (
        PipelineAction.REGENERATE_CONFIGS if all_failed
        else PipelineAction.CONTINUE
    )

    state.log_timing("critic", time.perf_counter() - t0)
    return state
