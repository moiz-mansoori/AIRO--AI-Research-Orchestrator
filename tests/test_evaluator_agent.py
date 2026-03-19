"""Tests for Evaluator Agent — AIRO"""
import pytest
from orchestrator.state import AIROState, TaskType, TrainingResult, CriticResult, CriticVerdict
from agents.evaluator_agent import evaluator_agent_node
import pandas as pd
from unittest.mock import patch

@pytest.fixture
def sample_state():
    state = AIROState(task_type=TaskType.CLASSIFICATION)
    state.training_results = [
        TrainingResult(
            run_id="r1", config_id="c0", model_type="LogisticRegression", 
            val_metrics={"f1_macro": 0.70}, status="COMPLETED"
        ),
        TrainingResult(
            run_id="r2", config_id="c1", model_type="RandomForest", 
            val_metrics={"f1_macro": 0.85}, status="COMPLETED"
        ),
        TrainingResult(
            run_id="r3", config_id="c2", model_type="MLP", 
            val_metrics={"f1_macro": 0.82}, status="COMPLETED"
        )
    ]
    state.critic_results = [
        CriticResult(run_id="r1", verdict=CriticVerdict.PASS, issues=[], recommendations=[]),
        CriticResult(run_id="r2", verdict=CriticVerdict.PASS, issues=[], recommendations=[]),
        CriticResult(run_id="r3", verdict=CriticVerdict.PASS, issues=[], recommendations=[])
    ]
    return state

@patch("tools.llm_tools.call_llm_for_selection_reasoning")
def test_evaluator_ranks_correctly_and_selects_best(mock_llm, sample_state):
    mock_llm.return_value = "Selected RandomForest for highest f1_macro."
    state = evaluator_agent_node(sample_state)
    
    assert len(state.leaderboard) == 3
    # RandomForest should be rank 1 (0.85)
    assert state.leaderboard[0].model_type == "RandomForest"
    assert state.leaderboard[0].primary_metric == 0.85
    assert state.best_model_type == "RandomForest"
    assert state.best_run_id == "r2"
    
def test_evaluator_calculates_baseline_improvement(sample_state):
    with patch("tools.llm_tools.call_llm_for_selection_reasoning", return_value="Test"):
        state = evaluator_agent_node(sample_state)
        # Baseline is 0.70. Best is 0.85. 
        # Improvement: (0.85 - 0.70) / 0.70 * 100 = 21.43%
        assert round(state.improvement_over_baseline_pct, 2) == 21.43
