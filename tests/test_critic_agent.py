"""Tests for the Critic Agent — AIRO"""
import pytest
from orchestrator.state import AIROState, TaskType, TrainingResult, CriticVerdict
from agents.critic_agent import critic_agent_node, _audit_run


@pytest.fixture
def base_state() -> AIROState:
    state = AIROState(task_type=TaskType.CLASSIFICATION)
    state.split_sizes = {"train": 700, "val": 150, "test": 150}
    return state


def test_pass_verdict(base_state):
    run = TrainingResult(
        run_id="r1", config_id="cfg_0_baseline", model_type="LogisticRegression",
        status="COMPLETED",
        train_metrics={"f1_macro": 0.85},
        val_metrics={"f1_macro": 0.83},
    )
    base_state.training_results = [run]
    result = _audit_run("r1", base_state)
    assert result.verdict == CriticVerdict.PASS


def test_overfitting_detected(base_state):
    run = TrainingResult(
        run_id="r2", config_id="cfg_1", model_type="XGBoost",
        status="COMPLETED",
        train_metrics={"f1_macro": 0.99},
        val_metrics={"f1_macro": 0.70},
    )
    base_state.training_results = [run]
    result = _audit_run("r2", base_state)
    assert result.verdict == CriticVerdict.WARN
    assert any("Overfitting" in i for i in result.issues)


def test_leakage_detected(base_state):
    run = TrainingResult(
        run_id="r3", config_id="cfg_2", model_type="RandomForest",
        status="COMPLETED",
        train_metrics={"f1_macro": 0.80},
        val_metrics={"f1_macro": 0.92},
    )
    base_state.training_results = [run]
    result = _audit_run("r3", base_state)
    assert result.verdict == CriticVerdict.FAIL
    assert any("leakage" in i.lower() for i in result.issues)


def test_failed_training(base_state):
    run = TrainingResult(
        run_id="r4", config_id="cfg_3", model_type="MLP",
        status="FAILED", error_message="CUDA out of memory",
    )
    base_state.training_results = [run]
    result = _audit_run("r4", base_state)
    assert result.verdict == CriticVerdict.FAIL


def test_all_fail_triggers_regenerate(base_state):
    runs = [
        TrainingResult(run_id=f"r{i}", config_id=f"cfg_{i}", model_type="X",
                       status="FAILED", error_message="err")
        for i in range(3)
    ]
    base_state.training_results = runs
    updated = critic_agent_node(base_state)
    from orchestrator.state import PipelineAction
    assert updated.pipeline_action == PipelineAction.REGENERATE_CONFIGS
