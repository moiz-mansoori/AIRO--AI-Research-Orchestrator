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
from sklearn.preprocessing import LabelEncoder, StandardScaler, OrdinalEncoder

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
    Only handles dropping duplicates and basic type normalization.
    Imputation, scaling, and encoding are handled inside split_dataset
    to completely prevent data leakage.
    """
    df = df.drop_duplicates().reset_index(drop=True)

    # We construct the schema based on raw types (which lets the Config Agent
    # know what features are categorical/objects vs float/int numeric)
    feature_schema = {col: str(df[col].dtype) for col in df.columns}

    feature_cols = [c for c in df.columns if c != target_col]
    numeric_cols  = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
    cat_cols      = df[feature_cols].select_dtypes(exclude=[np.number]).columns.tolist()

    logger.info(f"Cleaned dataset (raw): {len(numeric_cols)} numeric, {len(cat_cols)} categorical features")
    return df, feature_schema

# Split 
def split_dataset(
    df: pd.DataFrame,
    target_col: str,
    task_type: TaskType,
    out_dir: str,
    random_state: int = 42,
) -> dict[str, int]:
    """
    Stratified 70/15/15 split. Imputes, encodes, and scales the splits
    by fitting ONLY on the training split, and applying (transforming) 
    to val/test splits to prevent data leakage.
    Saves parquet files. Returns split sizes.
    """
    X = df.drop(columns=[target_col])
    y = df[target_col]

    stratify = y if task_type == TaskType.CLASSIFICATION else None

    try:
        X_train, X_tmp, y_train, y_tmp = train_test_split(
            X, y, test_size=0.30, random_state=random_state, stratify=stratify
        )
    except ValueError as e:
        logger.warning(f"Stratified split failed ({e}) — falling back to random split.")
        stratify = None
        X_train, X_tmp, y_train, y_tmp = train_test_split(
            X, y, test_size=0.30, random_state=random_state, stratify=None
        )

    stratify2 = y_tmp if stratify is not None and task_type == TaskType.CLASSIFICATION else None
    try:
        X_val, X_test, y_val, y_test = train_test_split(
            X_tmp, y_tmp, test_size=0.50, random_state=random_state, stratify=stratify2
        )
    except ValueError:
        logger.warning(f"Stratified secondary split failed — falling back to random split.")
        X_val, X_test, y_val, y_test = train_test_split(
            X_tmp, y_tmp, test_size=0.50, random_state=random_state, stratify=None
        )

    # Preprocessing: Imputation, Encoding, Scaling (fit on train, transform on val/test)
    feature_cols = X_train.columns.tolist()
    numeric_cols  = X_train.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols      = X_train.select_dtypes(exclude=[np.number]).columns.tolist()

    # 1. Imputation
    # Numeric imputation using train median
    for col in numeric_cols:
        if X_train[col].isnull().any() or X_val[col].isnull().any() or X_test[col].isnull().any():
            median_val = X_train[col].median()
            # If median_val is NaN (all values in train are NaN), fallback to 0.0
            if pd.isna(median_val):
                median_val = 0.0
            X_train[col] = X_train[col].fillna(median_val)
            X_val[col] = X_val[col].fillna(median_val)
            X_test[col] = X_test[col].fillna(median_val)

    # Categorical imputation using train mode
    for col in cat_cols:
        if X_train[col].isnull().any() or X_val[col].isnull().any() or X_test[col].isnull().any():
            mode_series = X_train[col].mode()
            mode_val = mode_series[0] if not mode_series.empty else "missing"
            X_train[col] = X_train[col].fillna(mode_val)
            X_val[col] = X_val[col].fillna(mode_val)
            X_test[col] = X_test[col].fillna(mode_val)

    # 2. Categorical features encoding using OrdinalEncoder (safe unseen category handling)
    if cat_cols:
        oe = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
        # Convert to string to avoid comparison issues with mixed types
        X_train[cat_cols] = oe.fit_transform(X_train[cat_cols].astype(str))
        X_val[cat_cols]   = oe.transform(X_val[cat_cols].astype(str))
        X_test[cat_cols]  = oe.transform(X_test[cat_cols].astype(str))

    # 3. Target column encoding for classification
    if task_type == TaskType.CLASSIFICATION:
        le = LabelEncoder()
        # Convert target to string before encoding
        y_train = pd.Series(le.fit_transform(y_train.astype(str)), index=y_train.index, name=target_col)
        y_val   = pd.Series(le.transform(y_val.astype(str)), index=y_val.index, name=target_col)
        y_test  = pd.Series(le.transform(y_test.astype(str)), index=y_test.index, name=target_col)

    # 4. Standard Scaling of numeric features
    if numeric_cols:
        scaler = StandardScaler()
        X_train[numeric_cols] = scaler.fit_transform(X_train[numeric_cols])
        X_val[numeric_cols]   = scaler.transform(X_val[numeric_cols])
        X_test[numeric_cols]  = scaler.transform(X_test[numeric_cols])

    # Save to out_dir
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
