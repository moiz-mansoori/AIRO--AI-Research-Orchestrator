"""
AIRO — tools/mlflow_tools.py
MLflow helpers: run management, metric logging, artifact saving.
"""
from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any
import mlflow
import mlflow.sklearn
from loguru import logger
from orchestrator.state import ExperimentConfig

def get_or_create_experiment(name: str) -> str:
    """Return existing experiment ID or create a new one."""
    exp = mlflow.get_experiment_by_name(name)
    if exp is not None:
        return exp.experiment_id
    return mlflow.create_experiment(name)

def start_run(
    experiment_name: str,
    config: ExperimentConfig,
    tags: dict[str, str] | None = None,
) -> mlflow.ActiveRun:
    """Start a new MLflow run and log the config as params."""
    exp_id = get_or_create_experiment(experiment_name)
    run = mlflow.start_run(
        experiment_id=exp_id,
        run_name=f"{config.model_type}_{config.config_id}",
        tags={
            "airo.config_id":   config.config_id,
            "airo.model_type":  config.model_type,
            "airo.seed":        str(config.random_seed),
            **(tags or {}),
        },
    )
    # Log hyperparams
    flat_params = _flatten(config.hyperparams)
    flat_params["model_type"]   = config.model_type
    flat_params["random_seed"]  = str(config.random_seed)
    flat_params["feature_subset"] = (
        "all" if config.feature_subset == "all"
        else str(len(config.feature_subset))  # log count, not full list
    )
    mlflow.log_params(flat_params)
    logger.debug(f"MLflow run started: {run.info.run_id}")
    return run

def log_metrics(
    train_metrics: dict[str, float],
    val_metrics:   dict[str, float],
) -> None:
    mlflow.log_metrics({f"train_{k}": v for k, v in train_metrics.items()})
    mlflow.log_metrics({f"val_{k}":   v for k, v in val_metrics.items()})

def save_model(model: Any, run_id: str, models_dir: str = "models") -> str:
    """Pickle the model and log it as an MLflow artifact."""
    out_dir = Path(models_dir) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / "model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    mlflow.log_artifact(str(model_path), artifact_path="model")
    logger.debug(f"Model saved: {model_path}")
    return str(model_path)

def load_model(run_id: str, models_dir: str = "models") -> Any:
    model_path = Path(models_dir) / run_id / "model.pkl"
    with open(model_path, "rb") as f:
        return pickle.load(f)

def get_run_metrics(run_id: str) -> dict[str, float]:
    """Fetch logged metrics from a completed MLflow run."""
    client = mlflow.tracking.MlflowClient()
    run = client.get_run(run_id)
    return dict(run.data.metrics)

def log_figure(fig: Any, filename: str) -> None:
    """Log a matplotlib figure as an MLflow artifact."""
    import tempfile, matplotlib.pyplot as plt
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        fig.savefig(tmp.name, bbox_inches="tight", dpi=150)
        mlflow.log_artifact(tmp.name, artifact_path="plots")
    plt.close(fig)

# Helpers
def _flatten(d: dict, prefix: str = "") -> dict[str, str]:
    """Flatten nested dict for MLflow param logging (strings only)."""
    out: dict[str, str] = {}
    for k, v in d.items():
        key = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        else:
            out[key] = str(v)
    return out
