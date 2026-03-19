"""
AIRO — tools/metrics_tools.py
Unified metric computation for classification and regression.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from orchestrator.state import TaskType

def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    task_type: TaskType,
    y_prob: np.ndarray | None = None,
) -> dict[str, float]:
    """
    Compute all relevant metrics for the given task type.
    Returns a flat dict of metric_name → float.
    """
    if task_type == TaskType.CLASSIFICATION:
        return _classification_metrics(y_true, y_pred, y_prob)
    return _regression_metrics(y_true, y_pred)


def _classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray | None = None,
) -> dict[str, float]:
    metrics: dict[str, float] = {
        "accuracy":  round(float(accuracy_score(y_true, y_pred)), 4),
        "f1_macro":  round(float(f1_score(y_true, y_pred, average="macro",  zero_division=0)), 4),
        "f1_weighted": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
    }
    if y_prob is not None:
        try:
            n_classes = len(np.unique(y_true))
            auc = roc_auc_score(
                y_true, y_prob,
                multi_class="ovr" if n_classes > 2 else "raise",
                average="macro",
            )
            metrics["auc"] = round(float(auc), 4)
        except ValueError:
            pass  # AUC undefined for some edge cases
    return metrics


def _regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, float]:
    mse = mean_squared_error(y_true, y_pred)
    return {
        "rmse": round(float(np.sqrt(mse)), 4),
        "mae":  round(float(mean_absolute_error(y_true, y_pred)), 4),
        "r2":   round(float(r2_score(y_true, y_pred)), 4),
    }


def compute_learning_curve(
    model: object,
    X_train: np.ndarray,
    y_train: np.ndarray,
    task_type: TaskType,
    cv: int = 3,
    n_points: int = 5,
) -> dict[str, list[float]]:
    """
    Compute learning curve data points.
    cv=3, n_points=5 = 15 fits per model (was 40 with cv=5, n_points=8).
    n_jobs=1 avoids thread contention inside ThreadPoolExecutor.
    Set AIRO_SKIP_CURVES=true in .env to skip entirely.
    Returns {"train_sizes", "train_scores", "val_scores"}.
    """
    import os
    if os.getenv("AIRO_SKIP_CURVES", "false").lower() == "true":
        return {"train_sizes": [], "train_scores": [], "val_scores": []}

    from sklearn.model_selection import learning_curve

    scoring = "f1_macro" if task_type == TaskType.CLASSIFICATION else "neg_root_mean_squared_error"

    train_sizes_abs, train_scores, val_scores = learning_curve(
        model, X_train, y_train,
        cv=cv,
        scoring=scoring,
        train_sizes=np.linspace(0.2, 1.0, n_points),
        n_jobs=1,
    )

    return {
        "train_sizes": train_sizes_abs.tolist(),
        "train_scores": train_scores.mean(axis=1).tolist(),
        "val_scores":   val_scores.mean(axis=1).tolist(),
    }
