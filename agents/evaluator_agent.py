"""
AIRO — agents/evaluator_agent.py
Ranks all valid experiments and selects the best model.
"""
from __future__ import annotations
import time
from orchestrator.state import (
    AIROState, CriticVerdict, LeaderboardEntry, TaskType
)
from loguru import logger


def evaluator_agent_node(state: AIROState) -> AIROState:
    """
    LangGraph node: Evaluator Agent.

    Steps:
      1. Filter to PASS + WARN runs only
      2. Fetch full metrics from MLflow for each run
      3. Rank by primary metric (F1 macro for classification, RMSE↓ for regression)
      4. Build leaderboard and save as CSV
      5. Select best model + compute % improvement over baseline
      6. Write selection_reasoning via LLM call (3 sentences)
      7. Populate state.leaderboard, best_run_id, best_model_type,
         improvement_over_baseline_pct, selection_reasoning

    Returns updated AIROState.
    """
    t0 = time.perf_counter()
    state.current_agent = "evaluate"

    valid_runs = state.passed_runs()
    if not valid_runs:
        state.add_error("evaluate", "No valid runs to evaluate — all failed critic audit.")
        state.log_timing("evaluate", time.perf_counter() - t0)
        return state

    metric = state.primary_metric_name()
    reverse = state.task_type == TaskType.CLASSIFICATION  # higher is better for classification

    sorted_runs = sorted(
        valid_runs,
        key=lambda r: r.val_metrics.get(metric, 0.0),
        reverse=reverse,
    )

    leaderboard: list[LeaderboardEntry] = []
    for rank, run in enumerate(sorted_runs, start=1):
        verdict = next(
            (c.verdict for c in state.critic_results if c.run_id == run.run_id),
            CriticVerdict.PASS,
        )
        entry = LeaderboardEntry(
            rank=rank,
            run_id=run.run_id,
            model_type=run.model_type,
            primary_metric=run.val_metrics.get(metric, 0.0),
            secondary_metrics={k: v for k, v in run.val_metrics.items() if k != metric},
            verdict=verdict,
        )
        leaderboard.append(entry)

    state.leaderboard = leaderboard

    if leaderboard:
        best = leaderboard[0]
        state.best_run_id = best.run_id
        state.best_model_type = best.model_type

        # Baseline is always config #0
        baseline_run = next(
            (r for r in valid_runs if r.config_id and ("baseline" in r.config_id.lower() or r.config_id.endswith("_0") or r.config_id == "c0")),
            None,
        )
        
        state.improvement_over_baseline_pct = 0.0
        if baseline_run:
            baseline_m = baseline_run.val_metrics.get(metric, 1e-9)
            if reverse: # Classification (higher is better)
                state.improvement_over_baseline_pct = (
                    (best.primary_metric - baseline_m) / abs(baseline_m) * 100
                )
            else: # Regression (lower is better, so baseline - best)
                state.improvement_over_baseline_pct = (
                    (baseline_m - best.primary_metric) / abs(baseline_m) * 100
                )

        try:
            from tools.llm_tools import call_llm_for_selection_reasoning
            
            # create a mini summary of the leaderboard for the LLM
            lb_summary = "\n".join([f"Rank {e.rank}: {e.model_type} ({metric}={e.primary_metric:.4f})" for e in state.leaderboard[:3]])
            
            state.selection_reasoning = call_llm_for_selection_reasoning(
                best_model=best.model_type,
                metric_name=metric,
                metric_value=best.primary_metric,
                improvement_pct=state.improvement_over_baseline_pct,
                leaderboard_summary=lb_summary
            )
        except Exception as exc:
            import traceback
            logger.warning(
                f"[evaluator] LLM selection reasoning failed — "
                f"type={type(exc).__name__} msg={exc}. "
                f"Using fallback string. Full trace:\n{traceback.format_exc()}"
            )
            state.selection_reasoning = (
                f"{best.model_type} ranked #1 with {metric}={best.primary_metric:.4f} "
                f"across {len(state.leaderboard)} evaluated models "
                f"({state.improvement_over_baseline_pct:+.1f}% vs baseline)."
            )

    from tools.report_tools import save_leaderboard_csv
    csv_path = f"reports/{state.experiment_id}/leaderboard.csv"
    save_leaderboard_csv(state, csv_path)

    state.log_timing("evaluate", time.perf_counter() - t0)
    return state
