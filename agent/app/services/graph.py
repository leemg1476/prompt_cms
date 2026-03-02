from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.services.store import prompt_store


class AgentState(TypedDict):
    prompt_key: str
    user_input: str
    output: str


def _format_response(state: AgentState) -> AgentState:
    prompt = prompt_store.get(state["prompt_key"])
    state["output"] = (
        f"[prompt_key={prompt.prompt_key} version={prompt.version}] "
        f"{prompt.content.strip()} | user_input={state['user_input']}"
    )
    return state


def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("format_response", _format_response)
    workflow.set_entry_point("format_response")
    workflow.add_edge("format_response", END)
    return workflow.compile()


agent_graph = build_graph()
