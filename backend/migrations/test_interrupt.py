import sys
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

class State(TypedDict):
    value: str
    approved: bool

def step_1(state: State):
    print("Executing Step 1")
    return {"value": "hello"}

def step_hitl(state: State):
    print("Executing Step HITL")
    res = interrupt("Please approve this")
    print(f"Resumed with: {res}")
    return {"approved": res}

def step_2(state: State):
    print("Executing Step 2")
    return {"value": state["value"] + " world"}

workflow = StateGraph(State)
workflow.add_node("step_1", step_1)
workflow.add_node("step_hitl", step_hitl)
workflow.add_node("step_2", step_2)

workflow.add_edge(START, "step_1")
workflow.add_edge("step_1", "step_hitl")
workflow.add_edge("step_hitl", "step_2")
workflow.add_edge("step_2", END)

checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "1"}}

# Initial run
print("--- Starting first run ---")
try:
    res = graph.invoke({"value": "init", "approved": False}, config)
    print(f"Result: {res}")
except Exception as e:
    print(f"Exception raised: {type(e).__name__}: {e}")

# Check current state/interrupts
state = graph.get_state(config)
print(f"Current State tasks: {state.tasks}")

# Resume run
print("\n--- Resuming run ---")
try:
    from langgraph.types import Command
    res = graph.invoke(Command(resume=True), config)
    print(f"Resumed Result: {res}")
except Exception as e:
    print(f"Resumed Exception raised: {type(e).__name__}: {e}")

