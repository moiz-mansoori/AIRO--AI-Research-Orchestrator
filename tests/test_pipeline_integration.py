"""AIRO — tests/test_pipeline_integration.py
End-to-end smoke test using sklearn's iris dataset.
Mocks the LLM call so no API key is needed.
"""
import json
import os
import pytest
from unittest.mock import patch


MOCK_CONFIGS = json.dumps([
    {
        "config_id": "test_cfg_0",
        "model_type": "LogisticRegression",
        "hyperparams": {"max_iter": 200},
        "feature_subset": "all",
        "random_seed": 42,
        "notes": "Baseline",
    },
    {
        "config_id": "test_cfg_1",
        "model_type": "RandomForestClassifier",
        "hyperparams": {"n_estimators": 20, "max_depth": 4},
        "feature_subset": "all",
        "random_seed": 42,
        "notes": "RF config",
    },
])


@pytest.fixture
def iris_csv(tmp_path):
    from sklearn.datasets import load_iris
    import pandas as pd
    iris = load_iris(as_frame=True)
    df = iris.frame.rename(columns={"target": "species"})
    path = tmp_path / "iris.csv"
    df.to_csv(path, index=False)
    return str(path)


@pytest.fixture(autouse=True)
def set_dirs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for d in ["data/raw", "data/processed", "data/splits", "models", "reports", "logs", "prompts"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    (tmp_path / "prompts" / "system_prompt.txt").write_text("You are AIRO.")
    os.environ["MLFLOW_TRACKING_URI"] = f"sqlite:///{tmp_path}/mlruns.db"
    os.environ.setdefault("GROQ_API_KEY", "test-key")


def test_full_pipeline_smoke(iris_csv):
    """Full pipeline runs without crash. LLM calls are mocked."""
    import sys
    from pathlib import Path
    root = Path(__file__).parent.parent
    sys.path.insert(0, str(root))

    # Import modules FIRST to avoid circular import during patch resolution
    from orchestrator.graph import compile_graph
    from orchestrator.state import AIROState, TaskType, ComputeBudget, CriticVerdict
    import agents.config_agent as _config_mod
    import agents.evaluator_agent as _eval_mod
    import agents.reporter_agent as _report_mod
    import tools.llm_tools as _llm_mod

    # Now patch at the call sites using patch.object (no import resolution needed)
    with patch.object(_config_mod, "call_llm_for_configs", return_value=MOCK_CONFIGS), \
         patch.object(_llm_mod, "call_llm_for_selection_reasoning", return_value="Test reasoning."), \
         patch.object(_llm_mod, "call_llm_for_report_narrative", return_value="Test summary."), \
         patch.object(_llm_mod, "call_llm", return_value=json.dumps(["rec1", "rec2", "rec3", "rec4", "rec5"])):

        state = AIROState(
            dataset_path   = iris_csv,
            task_type      = TaskType.CLASSIFICATION,
            target_column  = "species",
            compute_budget = ComputeBudget.FAST,
        )

        graph = compile_graph()
        final = graph.invoke(state, config={"recursion_limit": 50})

        # LangGraph returns a dict, not an AIROState dataclass
        assert final["artifact_path"] != ""
        assert len(final["training_results"]) > 0
        assert len(final["critic_results"]) > 0
        assert final["report_md_path"] != ""

        # At least one run should pass or warn
        assert any(r.verdict in (CriticVerdict.PASS, CriticVerdict.WARN) for r in final["critic_results"])

