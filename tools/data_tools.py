"""
AIRO — tools/data_tools.py
Data ingestion, validation, cleaning, splitting, and DVC versioning.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

from orchestrator.state import DataQualityReport, TaskType

# Load 
def load_dataset(path: str) -> pd.DataFrame:
    p = Path(path)
    loaders = {".csv": pd.read_csv, ".parquet": pd.read_parquet, ".json": pd.read_json}
    loader = loaders.get(p.suffix.lower())
    if loader is None:
        raise ValueError(f"Unsupported file type: {p.suffix}. Use CSV, parquet, or JSON.")
    df = loader(p)
    logger.info(f"Loaded {p.name}: {df.shape[0]} rows × {df.shape[1]} cols")
    return df

# Validate 
def validate_dataset(
    df: pd.DataFrame,
    target_col: str,
    task_type: TaskType,
) -> DataQualityReport:
    report = DataQualityReport()
    report.row_count     = len(df)
    report.feature_count = df.shape[1] - 1  # exclude target

    # Null percentages
    report.null_pct = (df.isnull().mean() * 100).round(2).to_dict()

    # Duplicates
    report.duplicate_rows = int(df.duplicated().sum())

    # Class distribution (classification only)
    if task_type == TaskType.CLASSIFICATION and target_col in df.columns:
        vc = df[target_col].value_counts()
        report.class_distribution = vc.to_dict()
        if len(vc) > 1:
            report.imbalance_ratio = round(float(vc.max() / vc.min()), 2)
            if report.imbalance_ratio > 5:
                report.warnings.append(
                    f"Class imbalance detected — ratio={report.imbalance_ratio:.1f}. "
                    "Consider SMOTE or class_weight='balanced'."
                )

    # Critical warnings
    if report.row_count < 50:
        report.warnings.append("CRITICAL: Dataset has fewer than 50 rows — results will be unreliable.")
    if target_col not in df.columns:
        report.warnings.append(f"CRITICAL: Target column '{target_col}' not found in dataset.")

    high_null_cols = [c for c, pct in report.null_pct.items() if pct > 30]
    if high_null_cols:
        report.warnings.append(
            f"High missingness (>30%) in columns: {high_null_cols}. "
            "These rows were NOT dropped — handle with imputation."
        )

    if report.duplicate_rows > 0:
        report.warnings.append(f"{report.duplicate_rows} duplicate rows detected and removed.")

    return report

# Clean 
def clean_dataset(
    df: pd.DataFrame,
    target_col: str,
    task_type: TaskType,
) -> tuple[pd.DataFrame, dict[str, str]]:
    """
    Returns (cleaned_df, feature_schema).
    feature_schema maps column name → dtype string.
    """
    df = df.drop_duplicates().reset_index(drop=True)

    feature_cols = [c for c in df.columns if c != target_col]
    numeric_cols  = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
    cat_cols      = df[feature_cols].select_dtypes(exclude=[np.number]).columns.tolist()

    # Impute
    for col in numeric_cols:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].median())

    for col in cat_cols:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].mode()[0])

    # Encode categoricals
    le = LabelEncoder()
    for col in cat_cols:
        df[col] = le.fit_transform(df[col].astype(str))

    # Encode target for classification
    if task_type == TaskType.CLASSIFICATION and df[target_col].dtype == object:
        df[target_col] = le.fit_transform(df[target_col].astype(str))

    # Scale numerics (fit on full df here; re-fit on train only in training agent)
    scaler = StandardScaler()
    if numeric_cols:
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

    feature_schema = {col: str(df[col].dtype) for col in df.columns}
    logger.info(f"Cleaned dataset: {len(numeric_cols)} numeric, {len(cat_cols)} categorical features")
    return df, feature_schema

# Split 
def split_dataset(
    df: pd.DataFrame,
    target_col: str,
    task_type: TaskType,
    out_dir: str,
    random_state: int = 42,
) -> dict[str, int]:
    """Stratified 70/15/15 split. Saves parquet files. Returns split sizes."""
    X = df.drop(columns=[target_col])
    y = df[target_col]

    stratify = y if task_type == TaskType.CLASSIFICATION else None

    X_train, X_tmp, y_train, y_tmp = train_test_split(
        X, y, test_size=0.30, random_state=random_state, stratify=stratify
    )
    stratify2 = y_tmp if task_type == TaskType.CLASSIFICATION else None
    X_val, X_test, y_val, y_test = train_test_split(
        X_tmp, y_tmp, test_size=0.50, random_state=random_state, stratify=stratify2
    )

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    for split_name, (Xs, ys) in zip(
        ["train", "val", "test"],
        [(X_train, y_train), (X_val, y_val), (X_test, y_test)],
    ):
        split_df = pd.concat([Xs, ys], axis=1)
        split_df.to_parquet(out / f"{split_name}.parquet", index=False)

    sizes = {"train": len(X_train), "val": len(X_val), "test": len(X_test)}
    logger.info(f"Split sizes — {sizes}")
    return sizes

# DVC versioning 
def version_artifact(path: str) -> str:
    """
    Compute SHA-256 hash of the artifact for reproducibility tracking.
    Optionally runs `dvc add` if DVC is initialised in the project.
    Returns the file hash.
    """
    file_hash = _sha256(path)

    try:
        result = subprocess.run(
            ["dvc", "add", path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            logger.info(f"DVC: versioned {path} (sha256={file_hash[:12]}...)")
        else:
            logger.warning(f"DVC not initialised — skipping dvc add. Hash={file_hash[:12]}...")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        logger.warning("DVC not found — artifact hash stored in state only.")

    return file_hash


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# High-level pipeline call 
def run_data_pipeline(
    dataset_path: str,
    target_col: str,
    task_type: TaskType,
    experiment_id: str,
    processed_dir: str = "data/processed",
    splits_dir: str = "data/splits",
) -> dict[str, Any]:
    """
    Full data pipeline. Returns dict with all outputs needed by AIROState.
    """
    df_raw = load_dataset(dataset_path)
    quality_report = validate_dataset(df_raw, target_col, task_type)

    df_clean, feature_schema = clean_dataset(df_raw, target_col, task_type)

    artifact_path = str(Path(processed_dir) / f"{experiment_id}_clean.parquet")
    Path(processed_dir).mkdir(parents=True, exist_ok=True)
    df_clean.to_parquet(artifact_path, index=False)

    artifact_hash = version_artifact(artifact_path)
    quality_report.warnings.append(f"Artifact SHA-256: {artifact_hash[:16]}...")

    split_sizes = split_dataset(df_clean, target_col, task_type, splits_dir)

    return {
        "artifact_path":  artifact_path,
        "feature_schema": feature_schema,
        "quality_report": quality_report,
        "split_sizes":    split_sizes,
    }
