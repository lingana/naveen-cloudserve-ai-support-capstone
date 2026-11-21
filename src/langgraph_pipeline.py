from typing import TypedDict, Any, Dict, List

from langgraph.graph import StateGraph, END


class PipelineState(TypedDict, total=False):
    raw: Dict[str, Any]
    ticket: Any
    classification: Dict[str, Any]
    passages: List[Any]
    route_action: str
    route_reason: str
    answer: str
    citations: List[Dict[str, Any]]
    guardrails: List[str]
    result: Dict[str, Any]


def build_langgraph_pipeline(pipeline):
    graph = StateGraph(PipelineState)

    def ingest(state):
        ticket = pipeline.ingest(state["raw"])
        return {"ticket": ticket}

    def classify(state):
        classification = pipeline.classify(state["ticket"])
        return {"classification": classification}

    def retrieve(state):
        passages = pipeline.retrieve(state["ticket"])
        return {"passages": passages}

    def route(state):
        action, reason = pipeline.route(state["ticket"], state["classification"], state["passages"])
        return {"route_action": action, "route_reason": reason}

    def generate(state):
        answer, citations, uncertainty = pipeline.generate(state["ticket"], state["classification"], state["passages"])
        return {"answer": answer, "citations": citations}

    def validate(state):
        guard_status, findings = pipeline.validate(state.get("answer", ""), state["passages"])
        if guard_status == "block":
            return {"route_action": "blocked", "guardrails": findings}
        return {"guardrails": findings}

    def finalize(state):
        result = pipeline.finalize(state)
        return {"result": result}

    graph.add_node("ingest", ingest)
    graph.add_node("classify", classify)
    graph.add_node("retrieve", retrieve)
    graph.add_node("route", route)
    graph.add_node("generate", generate)
    graph.add_node("validate", validate)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "classify")
    graph.add_edge("classify", "retrieve")
    graph.add_edge("retrieve", "route")
    graph.add_conditional_edges("route", lambda state: "generate" if state["route_action"] == "answer" else "finalize")
    graph.add_edge("generate", "validate")
    graph.add_edge("validate", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()
