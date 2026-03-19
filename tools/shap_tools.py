"""
AIRO — tools/shap_tools.py
SHAP-based explainability: summary plots, top feature extraction.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from loguru import logger

def compute_shap_values(
    model: Any,
    X: pd.DataFrame,
    max_samples: int = 200,
) -> shap.Explanation | np.ndarray:
    """
    Auto-selects the right SHAP explainer for the model type.
    Subsample X for speed if it's large.
    """
    if len(X) > max_samples:
        X = X.sample(max_samples, random_state=42)

    model_class = type(model).__name__

    try:
        if model_class in ("XGBClassifier", "XGBRegressor",
                           "LGBMClassifier", "LGBMRegressor",
                           "RandomForestClassifier", "RandomForestRegressor",
                           "GradientBoostingClassifier", "GradientBoostingRegressor"):
            explainer = shap.TreeExplainer(model)
        else:
            explainer = shap.Explainer(model, X)

        return explainer(X)

    except Exception as exc:
        logger.warning(f"SHAP computation failed ({exc}). Returning zeros.")
        return np.zeros((len(X), X.shape[1]))


def top_features(
    shap_values: Any,
    feature_names: list[str],
    top_n: int = 10,
) -> list[dict[str, float]]:
    """Return top_n features ranked by mean absolute SHAP value."""
    if isinstance(shap_values, shap.Explanation):
        vals = np.abs(shap_values.values)
        if vals.ndim == 3:          # multi-class: average across classes
            vals = vals.mean(axis=2)
        mean_abs = vals.mean(axis=0)
    else:
        mean_abs = np.abs(shap_values).mean(axis=0)

    ranked = sorted(
        zip(feature_names, mean_abs.tolist()),
        key=lambda x: x[1], reverse=True
    )[:top_n]

    return [{"feature": f, "importance": round(v, 4)} for f, v in ranked]


def save_shap_summary_plot(
    shap_values: Any,
    X: pd.DataFrame,
    out_path: str,
    title: str = "SHAP Feature Importance",
) -> str:
    """Save a SHAP summary (bar) plot to disk. Returns the path."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    shap.summary_plot(shap_values, X, plot_type="bar", show=False)
    plt.title(title, fontsize=13)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"SHAP summary plot saved: {out_path}")
    return out_path


def save_learning_curve_plot(
    curve_data: dict[str, list[float]],
    out_path: str,
    model_type: str = "",
) -> str:
    """Save a train vs val learning curve plot. Returns the path."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(curve_data["train_sizes"], curve_data["train_scores"], "o-", label="Train", color="#4F46E5")
    ax.plot(curve_data["train_sizes"], curve_data["val_scores"],   "o-", label="Val",   color="#0F766E")
    ax.set_xlabel("Training samples")
    ax.set_ylabel("Score")
    ax.set_title(f"Learning Curve — {model_type}", fontsize=12)
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    return out_path
