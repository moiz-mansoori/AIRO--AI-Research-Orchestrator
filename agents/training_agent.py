"""
AIRO — agents/training_agent.py
Executes all experiment configs in parallel using concurrent.futures.
Each config maps to one MLflow run.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import mlflow
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.svm import LinearSVC
from orchestrator.state import AIROState, ExperimentConfig, TaskType, TrainingResult
from tools.metrics_tools import compute_metrics, compute_learning_curve
from tools.mlflow_tools import log_metrics, save_model, start_run, log_figure
from tools.shap_tools import save_learning_curve_plot

MODEL_REGISTRY: dict[str, type] = {
    "LogisticRegression":          LogisticRegression,
    "Ridge":                       Ridge,
    "RandomForestClassifier":      RandomForestClassifier,
    "RandomForestRegressor":       RandomForestRegressor,
    "GradientBoostingClassifier":  GradientBoostingClassifier,
    "GradientBoostingRegressor":   GradientBoostingRegressor,
    "MLPClassifier":               MLPClassifier,
    "MLPRegressor":                MLPRegressor,
    "LinearSVC":                   LinearSVC,
}

try:
    from xgboost import XGBClassifier, XGBRegressor
    MODEL_REGISTRY["XGBClassifier"] = XGBClassifier
    MODEL_REGISTRY["XGBRegressor"]  = XGBRegressor
except ImportError:
    pass

def _load_splits(splits_dir: str, feature_subset: list[str] | str) -> tuple:
    train = pd.read_parquet(f"{splits_dir}/train.parquet")
    val   = pd.read_parquet(f"{splits_dir}/val.parquet")

    target = train.columns[-1]   # last column is always target
    X_train, y_train = train.drop(columns=[target]), train[target]
    X_val,   y_val   = val.drop(columns=[target]),   val[target]

    if feature_subset != "all" and isinstance(feature_subset, list):
        valid_cols = [c for c in feature_subset if c in X_train.columns]
        X_train, X_val = X_train[valid_cols], X_val[valid_cols]

    return X_train, y_train, X_val, y_val, target

def _train_single(
    config: ExperimentConfig,
    state: AIROState,
    experiment_name: str,
    splits_dir: str,
) -> TrainingResult:
    result = TrainingResult(config_id=config.config_id, model_type=config.model_type)
    run_ctx = None

    try:
        X_train, y_train, X_val, y_val, _ = _load_splits(splits_dir, config.feature_subset)

        ModelClass = MODEL_REGISTRY.get(config.model_type)
        if ModelClass is None:
            raise ValueError(f"Unknown model_type: {config.model_type}")

        hyperparams = {**config.hyperparams, "random_state": config.random_seed} \
            if "random_state" in ModelClass().get_params() else config.hyperparams

        model = ModelClass(**hyperparams)

        run_ctx = start_run(experiment_name, config)
        result.run_id = run_ctx.info.run_id

        t_start = time.perf_counter()
        model.fit(X_train, y_train)
        result.training_time_s = round(time.perf_counter() - t_start, 2)

        y_prob_train = y_prob_val = None
        if hasattr(model, "predict_proba"):
            y_prob_train = model.predict_proba(X_train)
            y_prob_val   = model.predict_proba(X_val)

        result.train_metrics = compute_metrics(y_train.values, model.predict(X_train), state.task_type, y_prob_train)
        result.val_metrics   = compute_metrics(y_val.values,   model.predict(X_val),   state.task_type, y_prob_val)

        log_metrics(result.train_metrics, result.val_metrics)
        mlflow.log_metric("training_time_s", result.training_time_s)

        # Learning curve
        try:
            curve_data = compute_learning_curve(model, X_train.values, y_train.values, state.task_type)
            curve_path = f"reports/{state.experiment_id}/learning_curves/{result.run_id}_curve.json"
            Path(curve_path).parent.mkdir(parents=True, exist_ok=True)
            with open(curve_path, "w", encoding="utf-8") as f:
                import json
                json.dump(curve_data, f)
            mlflow.log_artifact(curve_path, artifact_path="learning_curves")
        except Exception as exc:
            logger.warning(f"[train] Learning curve calculation failed: {exc}")

        result.model_artifact_path = save_model(model, result.run_id)
        result.status = "COMPLETED"
        mlflow.end_run()

        logger.info(f"[train] ✓ {config.model_type} run={result.run_id[:8]} "
                    f"val_{state.primary_metric_name()}={result.val_metrics.get(state.primary_metric_name(), 0):.4f}")

    except Exception as exc:
        result.status        = "FAILED"
        result.error_message = str(exc)
        logger.warning(f"[train] ✗ {config.model_type} failed: {exc}")
        try:
            mlflow.end_run(status="FAILED")
        except Exception:
            pass
    return result

def training_agent_node(state: AIROState) -> AIROState:
    t0 = time.perf_counter()
    state.current_agent = "train"
    max_workers     = int(os.getenv("AIRO_PARALLEL_WORKERS", "4"))
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "airo")
    splits_dir      = "data/splits"

    logger.info(f"[train] Training {len(state.configs)} configs with {max_workers} workers")

    import contextvars
    results: list[TrainingResult] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(contextvars.copy_context().run, _train_single, cfg, state, experiment_name, splits_dir): cfg
            for cfg in state.configs
        }
        for future in as_completed(futures):
            results.append(future.result())

    state.training_results = results
    n_ok   = sum(1 for r in results if r.status == "COMPLETED")
    n_fail = sum(1 for r in results if r.status == "FAILED")
    logger.info(f"[train] ✓ {n_ok} completed, {n_fail} failed")

    state.log_timing("train", time.perf_counter() - t0)
    return state
