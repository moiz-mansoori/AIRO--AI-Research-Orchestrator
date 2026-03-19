"""
AIRO — orchestrator/router.py

Conditional routing logic for the LangGraph StateMachine.
"""
from __future__ import annotations
import os
from orchestrator.state import AIROState, PipelineAction

def route_after_data(state: AIROState) -> str:
    """Stop the pipeline if data quality is critically bad."""
    critical = [w for w in state.quality_report.warnings if w.startswith("CRITICAL")]
    if critical:
        return "stop"
    return "config"

def route_after_critic(state: AIROState) -> str:
    """
    If all experiments failed the critic and we haven't retried yet,
    regenerate configs and retrain. Otherwise proceed to evaluation.
    """
    if (
        state.pipeline_action == PipelineAction.REGENERATE_CONFIGS
        and state.retry_count < int(os.getenv("AIRO_MAX_RETRIES", "1"))
    ):
        state.retry_count += 1
        return "regenerate"
    return "evaluate"
