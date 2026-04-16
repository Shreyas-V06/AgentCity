import operator
import json
from typing import List, Dict, Any, Annotated
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send
from typing_extensions import TypedDict

from db import initialize_db, initialize_redis
from llm.factory import LLMFactory, LLMConfig, LLMProvider

# Define structured output
class EvaluationScore(BaseModel):
    happiness: float = Field(..., description="Happiness: -1 to 1 (in decimal points, precise up to 3 places)")
    angriness: float = Field(..., description="Angriness: -1 to 1 (in decimal points, precise up to 3 places)")
    loyalty_to_party: float = Field(..., description="Loyalty to party: -1 to 1 (in decimal points, precise up to 3 places)")

class EvaluationState(TypedDict):
    reactions: List[Dict[str, Any]]
    results: Annotated[List[Dict[str, Any]], operator.add]

class SingleEvaluationState(TypedDict):
    reaction: Dict[str, Any]

def _evaluate_single(state: SingleEvaluationState, structured_llm) -> dict:
    reaction = state["reaction"]
    reaction_text = reaction.get("base_reaction", "")
    
    prompt = f"Evaluate the following reaction for Happiness, Angriness, and Loyalty to party.\nReaction:\n{reaction_text}"
    score: EvaluationScore = structured_llm.invoke(prompt)
    
    return {
        "results": [{
            "event_id": reaction.get("event_id"),
            "agent_id": reaction.get("agent_id"),
            "base_reaction": reaction_text,
            "happiness": score.happiness,
            "angriness": score.angriness,
            "loyalty_to_party": score.loyalty_to_party
        }]
    }

def _fan_out_evaluations(state: EvaluationState) -> list:
    sends = []
    for r in state["reactions"]:
        sends.append(Send("evaluate", {"reaction": r}))
    return sends

def build_evaluation_graph(llm):
    structured_llm = llm.with_structured_output(EvaluationScore)
    
    def evaluate_node(state: SingleEvaluationState):
        return _evaluate_single(state, structured_llm)
        
    graph = StateGraph(EvaluationState)
    graph.add_node("evaluate", evaluate_node)
    graph.add_conditional_edges(START, _fan_out_evaluations, ["evaluate"])
    graph.add_edge("evaluate", END)
    
    return graph.compile()

def run_evaluation():
    db = initialize_db()
    redis_client = initialize_redis()
    
    # loads up all the base reactions from redis
    keys = redis_client.keys("base_reaction:*")
    reactions = []
    if keys:
        raw_reactions = redis_client.mget(keys)
        for raw in raw_reactions:
            if raw:
                reactions.append(json.loads(raw))
    
    if not reactions:
        print("No base reactions found to evaluate.")
        return
        
    config = LLMConfig(provider=LLMProvider.GROQ, model_name="llama-3.3-70b-versatile", temperature=0.1)
    llm = LLMFactory.build(config)
    
    graph = build_evaluation_graph(llm)
    
    print(f"Evaluating {len(reactions)} reactions parallely...")
    final_state = graph.invoke({"reactions": reactions})
    results = final_state.get("results", [])
    
    if results:
        # just push into database at the end
        db.evaluations.insert_many(results)
        print(f"Successfully pushed {len(results)} evaluated reactions into the 'evaluations' collection.")

if __name__ == "__main__":
    run_evaluation()