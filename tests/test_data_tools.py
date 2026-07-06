"""Tests for Data Tools — AIRO"""
import pytest
import pandas as pd
import numpy as np
from orchestrator.state import TaskType, DataQualityReport
from tools.data_tools import validate_dataset, clean_dataset, split_dataset, _sha256


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


def test_clean_returns_raw_types(sample_df):
    cleaned, schema = clean_dataset(sample_df, "target", TaskType.CLASSIFICATION)
    assert cleaned["gender"].dtype == object


def test_split_dataset_imputes_encodes_and_scales(sample_df, tmp_path):
    sample_df.loc[0:10, "age"] = np.nan
    cleaned, schema = clean_dataset(sample_df, "target", TaskType.CLASSIFICATION)
    
    splits_dir = tmp_path / "splits"
    sizes = split_dataset(cleaned, "target", TaskType.CLASSIFICATION, str(splits_dir))
    
    train = pd.read_parquet(splits_dir / "train.parquet")
    val = pd.read_parquet(splits_dir / "val.parquet")
    test = pd.read_parquet(splits_dir / "test.parquet")
    
    assert train.isnull().sum().sum() == 0
    assert val.isnull().sum().sum() == 0
    assert test.isnull().sum().sum() == 0
    
    assert train["gender"].dtype in [np.float32, np.float64, np.int32, np.int64, np.int8]
    assert val["gender"].dtype in [np.float32, np.float64, np.int32, np.int64, np.int8]
    assert train["target"].dtype in [np.int32, np.int64, np.int8]
