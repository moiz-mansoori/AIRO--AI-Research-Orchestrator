"""
AIRO — agents/config_agent.py
Generates N diverse experiment configs using LLM reasoning + Optuna search spaces.
"""
from __future__ import annotations

import json
import time
import uuid

from loguru import logger

from orchestrator.state import AIROState, ComputeBudget, ExperimentConfig, TaskType
from tools.llm_tools import call_llm_for_configs


BUDGET_N_CONFIGS = {
    ComputeBudget.FAST:       3,
    ComputeBudget.STANDARD:   6,
    ComputeBudget.EXHAUSTIVE: 10,
}


def config_agent_node(state: AIROState) -> AIROState:
    """
    LangGraph node: Config Generator Agent.
    Calls Groq LLM to generate N diverse experiment configs.
    Config #0 is always a naive baseline.
    Falls back to 3 hardcoded configs if LLM fails.
    """
    t0 = time.perf_counter()
    state.current_agent = "config"
    n = BUDGET_N_CONFIGS[state.compute_budget]
    logger.info(f"[config] Generating {n} configs (budget={state.compute_budget})")

    llm_succeeded = False
    try:
        raw_json = call_llm_for_configs(
            feature_schema=state.feature_schema,
            task_type=state.task_type,
            n_configs=n,
        )
        logger.debug(f"[config] LLM raw response (first 300 chars): {raw_json[:300]}")
        configs_raw: list[dict] = json.loads(raw_json)

        configs = []
        for i, c in enumerate(configs_raw):
            cfg = ExperimentConfig(
                config_id      = f"{state.experiment_id}_cfg_{i}",
                model_type     = c.get("model_type", "LogisticRegression"),
                hyperparams    = c.get("hyperparams", {}),
                feature_subset = c.get("feature_subset", "all"),
                random_seed    = c.get("random_seed", 42),
                notes          = c.get("notes", ""),
            )
            configs.append(cfg)

        state.configs = configs
        llm_succeeded = True
        logger.info(f"[config] ✓ {len(configs)} configs — families: {list({c.model_type for c in configs})}")

    except json.JSONDecodeError as exc:
        logger.warning(f"[config] JSON parse failed: {exc}. Using fallback.")
        state.add_error("config", f"LLM JSON parse error: {exc}")

    except Exception as exc:
        logger.warning(f"[config] LLM call failed: {exc}. Using fallback.")
        state.add_error("config", f"LLM config error: {exc}")

    if not llm_succeeded:
        state.configs = _hardcoded_fallback_configs(
            state.experiment_id, state.task_type
        )
        logger.info(f"[config] Using {len(state.configs)} fallback configs: "
                     f"{[c.model_type for c in state.configs]}")

    state.log_timing("config", time.perf_counter() - t0)
    logger.info(f"[config] completed in {state.agent_timings['config']:.1f}s")
    return state


def _hardcoded_fallback_configs(
    experiment_id: str, task_type: str | TaskType
) -> list[ExperimentConfig]:
    """
    Return 3 diverse fallback configs when LLM config generation fails.
    Covers: linear baseline, ensemble (RF), gradient boosting (XGBoost).
    """
    is_clf = (task_type == TaskType.CLASSIFICATION
              or task_type == "classification")

    configs = [
        # Config 0 — Baseline (linear model)
        ExperimentConfig(
            config_id=f"{experiment_id}_cfg_0",
            model_type="LogisticRegression" if is_clf else "Ridge",
            hyperparams={"max_iter": 1000} if is_clf else {},
            feature_subset="all",
            random_seed=42,
            notes="Baseline — linear model, default params",
        ),
        # Config 1 — Random Forest (ensemble)
        ExperimentConfig(
            config_id=f"{experiment_id}_cfg_1",
            model_type="RandomForestClassifier" if is_clf else "RandomForestRegressor",
            hyperparams={"n_estimators": 100, "max_depth": 6},
            feature_subset="all",
            random_seed=42,
            notes="Fallback — Random Forest, moderate depth",
        ),
        # Config 2 — XGBoost (gradient boosting)
        ExperimentConfig(
            config_id=f"{experiment_id}_cfg_2",
            model_type="XGBClassifier" if is_clf else "XGBRegressor",
            hyperparams={
                "n_estimators": 100,
                "max_depth": 4,
                "learning_rate": 0.1,
                "verbosity": 0,
                "use_label_encoder": False,
                "eval_metric": "logloss" if is_clf else "rmse",
            },
            feature_subset="all",
            random_seed=42,
            notes="Fallback — XGBoost, standard params",
        ),
    ]
    return configs
