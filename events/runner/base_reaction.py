import json
import operator
from typing import List, Dict, Any, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send
from typing_extensions import TypedDict
from db import initialize_redis
from prompts import BASE_REACTION_PROMPT
from schemas.events import Event


class ReactionState(TypedDict):
    events: List[Event]
    results: Annotated[List[Dict[str, str]], operator.add]


class SingleReactionState(TypedDict):
    event: Event
    agent_data: Dict[str, Any]
    result: Dict[str, str]


def _load_agent_and_react(state: SingleReactionState, llm) -> dict:
    """Process a single event: load agent from Redis, call LLM, return result."""
    event = state["event"]
    agent_data = state["agent_data"]

    event_description = (
        " ".join(event.event_description)
        if isinstance(event.event_description, list)
        else event.event_description
    )

    prompt = BASE_REACTION_PROMPT.format(
        name=agent_data.get("name", "Unknown"),
        age=agent_data.get("age", "Unknown"),
        gender=agent_data.get("gender", "Unknown"),
        occupation=agent_data.get("occupation", "Unknown"),
        language=agent_data.get("language", "Unknown"),
        economic_background=agent_data.get("economic_background", "Unknown"),
        selfishness=agent_data.get("selfishness", "Unknown"),
        morality=agent_data.get("morality", "Unknown"),
        political_leaning=agent_data.get("political_leaning", "Unknown"),
        literacy=agent_data.get("literacy", "Unknown"),
        financial_score=agent_data.get("financial_score", "Unknown"),
        persona=agent_data.get("persona", "Unknown"),
        tone=agent_data.get("tone", "Unknown"),
        event_description=event_description,
    )

    response = llm.invoke(prompt)
    return {
        "results": [{
            "event_id": event.event_id,
            "base_reaction": response.content,
            "agent_id": event.agent_id,
        }]
    }


def _fan_out_events(state: ReactionState) -> list:
    """Fan out each event into a parallel branch with its agent data pre-loaded from Redis."""
    redis_client = initialize_redis()
    events = state["events"]

    agent_ids = list({e.agent_id for e in events})
    keys = [f"agent:{aid}" for aid in agent_ids]
    raw_values = redis_client.mget(keys)
    agent_cache = {}
    for aid, raw in zip(agent_ids, raw_values):
        if raw is not None:
            agent_cache[aid] = json.loads(raw)

    sends = []
    for event in events:
        agent_data = agent_cache.get(event.agent_id, {})
        sends.append(
            Send("react", {"event": event, "agent_data": agent_data})
        )
    return sends


def _build_reaction_graph(llm):
    """Build the LangGraph that fans out LLM calls in parallel."""

    def react_node(state: SingleReactionState) -> dict:
        return _load_agent_and_react(state, llm)

    graph = StateGraph(ReactionState)
    graph.add_node("react", react_node)

    graph.add_conditional_edges(START, _fan_out_events, ["react"])
    graph.add_edge("react", END)

    return graph.compile()


def generate_base_reactions(events: List[Event], llm) -> List[Dict[str, str]]:
    """
    Generate base reactions for a list of events in parallel using LangGraph.

    Each event's agent details are loaded from Redis, and all LLM calls are
    dispatched in parallel via LangGraph's Send/fan-out mechanism.

    Args:
        events: List of Event objects, each with an agent_id.
        llm: A LangChain-compatible chat model (e.g. from LLMFactory.build).

    Returns:
        List of dicts with keys: event_id, base_reaction, agent_id.
    """
    app = _build_reaction_graph(llm)
    result = app.invoke({"events": events, "results": []})
    return result["results"]
