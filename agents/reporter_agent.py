"""
AIRO — agents/reporter_agent.py
Generates the full experiment report (Markdown + PDF).
"""
from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from loguru import logger

from orchestrator.state import AIROState
from tools.llm_tools import call_llm, call_llm_for_report_narrative, call_llm_for_selection_reasoning
from tools.mlflow_tools import load_model
from tools.report_tools import render_markdown, render_pdf, save_leaderboard_csv, save_markdown
from tools.shap_tools import compute_shap_values, save_shap_summary_plot, top_features


def reporter_agent_node(state: AIROState) -> AIROState:
    t0 = time.perf_counter()
    state.current_agent = "report"
    report_dir = Path(f"reports/{state.experiment_id}")
    report_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"[report] Generating report → {report_dir}")

    # 1. SHAP explainability (skippable via env var)
    shap_top: list[dict] = []
    skip_shap = os.getenv("AIRO_SKIP_SHAP", "false").lower() == "true"
    if state.best_run_id and not skip_shap:
        try:
            import pandas as pd
            model    = load_model(state.best_run_id)
            val_df   = pd.read_parquet("data/splits/val.parquet")
            target   = val_df.columns[-1]
            X_val    = val_df.drop(columns=[target])
            sv       = compute_shap_values(model, X_val)
            shap_top = top_features(sv, X_val.columns.tolist())
        except Exception as exc:
            logger.warning(f"[report] SHAP skipped: {exc}")

    # Compile raw metrics (SHAP and Learning Curves) into a unified JSON file
    metrics_data = {
        "best_model_type": state.best_model_type,
        "best_run_id": state.best_run_id,
        "shap": shap_top,
        "learning_curve": None
    }
    if state.best_run_id:
        try:
            import json
            curve_json_path = Path(f"reports/{state.experiment_id}/learning_curves/{state.best_run_id}_curve.json")
            if curve_json_path.exists():
                with open(curve_json_path, "r", encoding="utf-8") as f:
                    metrics_data["learning_curve"] = json.load(f)
        except Exception as exc:
            logger.warning(f"[report] Failed to load learning curve JSON: {exc}")

    try:
        import json
        metrics_data_path = report_dir / "metrics_data.json"
        with open(metrics_data_path, "w", encoding="utf-8") as f:
            json.dump(metrics_data, f, indent=2)
        logger.info(f"[report] Saved unified metrics JSON to {metrics_data_path}")
    except Exception as exc:
        logger.warning(f"[report] Failed to save metrics JSON: {exc}")

    # 2-4. Parallel LLM calls — all 3 are independent
    exec_summary = ""
    selection_reason = ""
    recommendations: list[str] = []

    # Fallback values
    metric_val = f"{state.leaderboard[0].primary_metric:.4f}" if state.leaderboard else "N/A"
    default_exec_summary = (
        f"{state.best_model_type} achieved the best results "
        f"({state.primary_metric_name()}={metric_val}) "
        f"across {len(state.configs)} experiments."
    )
    default_recommendations = [
        "Try ensemble methods (stacking / blending) using the top-3 models.",
        "Apply SMOTE or class_weight='balanced' if class imbalance is present.",
        "Run Optuna hyperparameter search on the best model family.",
        "Engineer interaction features between the top-5 SHAP features.",
        "Use cross-validation (k=10) instead of a single val split for more stable estimates.",
    ]

    def _get_exec_summary():
        return call_llm_for_report_narrative(
            section="executive_summary",
            context={
                "best_model":    state.best_model_type,
                "metric":        state.primary_metric_name(),
                "metric_value":  state.leaderboard[0].primary_metric if state.leaderboard else "N/A",
                "improvement":   f"{state.improvement_over_baseline_pct:+.1f}%",
                "n_experiments": len(state.configs),
                "task_type":     state.task_type,
            },
        )

    def _get_recommendations():
        raw = call_llm(
            f"Give 5 concrete, specific ML recommendations to improve these results.\n"
            f"Best model: {state.best_model_type}, metric: {state.primary_metric_name()}.\n"
            f"Critic issues: {[r.issues for r in state.critic_results]}\n"
            f"Respond with ONLY a JSON array of 5 strings.",
            max_tokens=400,
            expect_json=True,
        )
        return json.loads(raw)

    def _get_reasoning():
        if not state.best_run_id:
            return ""
        if not state.selection_reasoning.endswith("pending implementation."):
            return state.selection_reasoning  # already set by evaluator
        leaderboard_summary = "\n".join(
            f"  {e.rank}. {e.model_type}: {e.primary_metric:.4f} ({e.verdict})"
            for e in state.leaderboard
        )
        return call_llm_for_selection_reasoning(
            best_model=state.best_model_type,
            metric_name=state.primary_metric_name(),
            metric_value=state.leaderboard[0].primary_metric if state.leaderboard else 0.0,
            improvement_pct=state.improvement_over_baseline_pct,
            leaderboard_summary=leaderboard_summary,
        )

    import contextvars
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(contextvars.copy_context().run, _get_exec_summary):    "summary",
            pool.submit(contextvars.copy_context().run, _get_recommendations): "recs",
            pool.submit(contextvars.copy_context().run, _get_reasoning):       "reasoning",
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                if name == "summary":
                    exec_summary = result
                elif name == "recs":
                    recommendations = result if isinstance(result, list) else []
                elif name == "reasoning":
                    selection_reason = result
            except Exception as exc:
                logger.warning(f"[report] LLM {name} failed: {exc}")

    # Apply results (with fallbacks)
    if not exec_summary:
        exec_summary = default_exec_summary
    if not recommendations:
        recommendations = default_recommendations
    if selection_reason:
        state.selection_reasoning = selection_reason

    # 5. DVC hash
    dvc_hash = "N/A"
    dvc_file = Path(state.artifact_path + ".dvc")
    if dvc_file.exists():
        import yaml
        try:
            dvc_data = yaml.safe_load(dvc_file.read_text())
            dvc_hash = dvc_data.get("outs", [{}])[0].get("md5", "N/A")
        except Exception:
            pass

    # 6. Render & save
    md_content = render_markdown(state, exec_summary, shap_top, recommendations, dvc_hash)

    state.report_md_path = save_markdown(md_content, str(report_dir / "airo_report.md"))
    state.report_pdf_path = render_pdf(state.report_md_path, str(report_dir / "airo_report.pdf"))
    state.leaderboard_csv_path = save_leaderboard_csv(state, str(report_dir / "leaderboard.csv"))

    logger.info(f"[report] ✓ Report ready → {state.report_pdf_path}")
    state.log_timing("report", time.perf_counter() - t0)
    return state
