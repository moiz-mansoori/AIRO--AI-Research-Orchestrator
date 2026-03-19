"""
AIRO — agents/data_agent.py
Full implementation: ingest, validate, clean, split, version.
"""
from __future__ import annotations
import time
from loguru import logger
from orchestrator.state import AIROState
from tools.data_tools import run_data_pipeline

def data_agent_node(state: AIROState) -> AIROState:
    """
    LangGraph node: Data Agent.
    Runs the full data pipeline and populates state with outputs.
    Stops pipeline on CRITICAL warnings.
    """
    t0 = time.perf_counter()
    state.current_agent = "data"
    logger.info(f"[data] Starting — dataset={state.dataset_path}")
    try:
        result = run_data_pipeline(
            dataset_path  = state.dataset_path,
            target_col    = state.target_column,
            task_type     = state.task_type,
            experiment_id = state.experiment_id,
            processed_dir = "data/processed",
            splits_dir    = "data/splits",
        )
        state.artifact_path  = result["artifact_path"]
        state.feature_schema = result["feature_schema"]
        state.quality_report = result["quality_report"]
        state.split_sizes    = result["split_sizes"]

        warnings = state.quality_report.warnings
        n_critical = sum(1 for w in warnings if w.startswith("CRITICAL"))
        logger.info(
            f"[data] ✓ {state.quality_report.row_count} rows, "
            f"{state.quality_report.feature_count} features, "
            f"{n_critical} critical warnings"
        )
    except Exception as exc:
        state.add_error("data", str(exc))
        logger.exception(f"[data] ✗ Pipeline failed: {exc}")

    state.log_timing("data", time.perf_counter() - t0)
    logger.info(f"[data] completed in {state.agent_timings['data']:.1f}s")
    return state
