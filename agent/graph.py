"""
LangGraph StateGraph definition for the hospital triage agent.

Graph:  START → intake → router → ward → doctor_assign → END
"""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import StateGraph, END

from agent.state import TriageState
from agent.nodes import (
    intake_node,
    router_node,
    ward_node,
    doctor_assign_node,
)


@lru_cache(maxsize=1)
def build_graph():
    """Compile and return the triage LangGraph. Cached — built only once."""
    builder = StateGraph(TriageState)

    # Register nodes
    builder.add_node("intake", intake_node)
    builder.add_node("router", router_node)
    builder.add_node("ward", ward_node)
    builder.add_node("doctor_assign", doctor_assign_node)

    # Linear edges
    builder.set_entry_point("intake")
    builder.add_edge("intake", "router")
    builder.add_edge("router", "ward")
    builder.add_edge("ward", "doctor_assign")
    builder.add_edge("doctor_assign", END)

    return builder.compile()
