"""
orchestrator/graph.py
LangGraph state machine. Defines all nodes, edges, and conditional routing.
"""

from __future__ import annotations
from langgraph.graph import END, START, StateGraph
from orchestrator.state import AIROState, PipelineAction
from agents.data_agent import data_agent_node
from orchestrator.router import route_after_data, route_after_critic
from agents.config_agent import config_agent_node
from agents.training_agent import training_agent_node
from agents.critic_agent import critic_agent_node
from agents.evaluator_agent import evaluator_agent_node
from agents.reporter_agent import reporter_agent_node

# Graph builder 
def build_graph() -> StateGraph:
    graph = StateGraph(AIROState)
    graph.add_node("data",      data_agent_node)
    graph.add_node("config",    config_agent_node)
    graph.add_node("train",     training_agent_node)
    graph.add_node("critic",    critic_agent_node)
    graph.add_node("evaluate",  evaluator_agent_node)
    graph.add_node("report",    reporter_agent_node)

    # Entry 
    graph.add_edge(START, "data")

    # Data → (conditional) 
    graph.add_conditional_edges(
        "data",
        route_after_data,
        {"config": "config", "stop": END},
    )

    # Config → Train → Critic 
    graph.add_edge("config", "train")
    graph.add_edge("train",  "critic")

    # Critic → (conditional: retry OR evaluate) 
    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {"regenerate": "config", "evaluate": "evaluate"},
    )
    # Evaluate → Report → END 
    graph.add_edge("evaluate", "report")
    graph.add_edge("report",   END)

    return graph

def compile_graph():
    """Compile and return the runnable AIRO graph."""
    return build_graph().compile()
