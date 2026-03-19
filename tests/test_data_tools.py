"""Tests for Data Tools — AIRO"""
import pytest
import pandas as pd
import numpy as np
from orchestrator.state import TaskType, DataQualityReport
from tools.data_tools import validate_dataset, clean_dataset, _sha256


@pytest.fixture
def sample_df():
    np.random.seed(42)
    return pd.DataFrame({
        "age":    np.random.randint(18, 80, 200).astype(float),
        "income": np.random.normal(50000, 15000, 200),
        "gender": np.random.choice(["M", "F"], 200),
        "target": np.random.choice([0, 1], 200),
    })


def test_validate_returns_report(sample_df):
    report = validate_dataset(sample_df, "target", TaskType.CLASSIFICATION)
    assert isinstance(report, DataQualityReport)
    assert report.row_count == 200
    assert report.feature_count == 3


def test_validate_detects_missing_target(sample_df):
    report = validate_dataset(sample_df, "nonexistent", TaskType.CLASSIFICATION)
    assert any("CRITICAL" in w for w in report.warnings)


def test_clean_encodes_categoricals(sample_df):
    cleaned, schema = clean_dataset(sample_df, "target", TaskType.CLASSIFICATION)
    assert cleaned["gender"].dtype in [np.int32, np.int64, np.int8]


def test_clean_no_nulls_after(sample_df):
    sample_df.loc[0:10, "age"] = np.nan
    cleaned, _ = clean_dataset(sample_df, "target", TaskType.CLASSIFICATION)
    assert cleaned.isnull().sum().sum() == 0
