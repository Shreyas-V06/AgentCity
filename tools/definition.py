import json
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from db import initialize_redis
from llm.factory import LLMConfig, LLMFactory, LLMProvider
from tools.arg_schemas import Decision, SocialMediaPost, ChatWithAgent
from prompts import CHAT_AGENT_INITIATE_PROMPT, CHAT_AGENT_RESPOND_PROMPT, CHAT_TARGET_RESPOND_PROMPT


class ChatResponse(BaseModel):
    reply: str = Field(description="The agent's message reply")
    end_conversation: bool = Field(description="Whether to end the conversation")

class ChatState(TypedDict):
    messages: List[str] 
    turn_count: int
    is_finished: bool

MAX_CHAT_TURNS = 15

def _build_chat_subgraph(agent_id: str, agent_data: dict, target_data: dict, event_id: str, event_description: str, initial_intent: str, redis_client):
    """Build a LangGraph subgraph for agent-to-agent conversation."""
    
    def main_agent_turn(state: ChatState) -> ChatState:
        """Main agent generates a response or initiates the conversation."""

        agent_name = agent_data.get("name", agent_id)
        target_name = target_data.get("name", target_data.get("agent_id", "Unknown"))
    
        agent_reaction_raw = redis_client.get(f"event:{event_id}:base_reaction:{agent_id}")
        agent_base_reaction = agent_reaction_raw if agent_reaction_raw else "No specific reaction."
        
        relations = agent_data.get("relations", {})
        relation = relations.get(target_data.get("agent_id"), "Acquaintance")
        
        history_str = "\n".join(state["messages"]) if state["messages"] else "[Conversation starting]"

        if len(state["messages"]) == 0:
            prompt = CHAT_AGENT_INITIATE_PROMPT.format(
                agent_name=agent_name,
                target_name=target_name,
                agent_occupation=agent_data.get("occupation", "Unknown"),
                agent_language=agent_data.get("language", "English"),
                agent_persona=agent_data.get("persona", "Average citizen"),
                agent_political_leaning=agent_data.get("political_leaning", 0.5),
                agent_morality=agent_data.get("morality", 0.5),
                agent_selfishness=agent_data.get("selfishness", 0.5),
                event_description=event_description,
                agent_base_reaction=agent_base_reaction,
                relation=relation,
                initial_intent=initial_intent
            )
        else:
            prompt = CHAT_AGENT_RESPOND_PROMPT.format(
                agent_name=agent_name,
                target_name=target_name,
                agent_occupation=agent_data.get("occupation", "Unknown"),
                agent_language=agent_data.get("language", "English"),
                agent_persona=agent_data.get("persona", "Average citizen"),
                agent_political_leaning=agent_data.get("political_leaning", 0.5),
                agent_morality=agent_data.get("morality", 0.5),
                agent_selfishness=agent_data.get("selfishness", 0.5),
                event_description=event_description,
                agent_base_reaction=agent_base_reaction,
                conversation_history=history_str
            )
        
        try:
            llm_config = LLMConfig(provider=LLMProvider.GROQ, model_name="llama-3.3-70b-versatile", temperature=0.7)
            llm = LLMFactory.build(llm_config)
        except BaseException:
            llm_config = LLMConfig(provider=LLMProvider.OPENAI, model_name="gpt-4o-mini", temperature=0.7)
            llm = LLMFactory.build(llm_config)
        
        structured_llm = llm.with_structured_output(ChatResponse)
        response = structured_llm.invoke(prompt)
        
        state["messages"].append(f"{agent_name}: {response.reply}")
        state["turn_count"] += 1
        state["is_finished"] = response.end_conversation
        
        return state
    
    def target_agent_turn(state: ChatState) -> ChatState:
        """Target agent generates a response."""
        agent_name = agent_data.get("name", agent_id)
        target_name = target_data.get("name", target_data.get("agent_id", "Unknown"))
        target_relations = target_data.get("relations", {})
        relation = target_relations.get(agent_id, "Acquaintance")
        history_str = "\n".join(state["messages"])
        
        prompt = CHAT_TARGET_RESPOND_PROMPT.format(
            target_name=target_name,
            agent_name=agent_name,
            target_occupation=target_data.get("occupation", "Unknown"),
            target_language=target_data.get("language", "English"),
            target_persona=target_data.get("persona", "Average citizen"),
            target_political_leaning=target_data.get("political_leaning", 0.5),
            target_morality=target_data.get("morality", 0.5),
            target_selfishness=target_data.get("selfishness", 0.5),
            event_description=event_description,
            conversation_history=history_str,
            relation=relation
        )
        
        try:
            llm_config = LLMConfig(provider=LLMProvider.GROQ, model_name="llama-3.3-70b-versatile", temperature=0.7)
            llm = LLMFactory.build(llm_config)
        except BaseException:
            llm_config = LLMConfig(provider=LLMProvider.OPENAI, model_name="gpt-4o-mini", temperature=0.7)
            llm = LLMFactory.build(llm_config)
    
        structured_llm = llm.with_structured_output(ChatResponse)
        response = structured_llm.invoke(prompt)
        
        state["messages"].append(f"{target_name}: {response.reply}")
        state["turn_count"] += 1
        state["is_finished"] = response.end_conversation
        
        return state
    
    def should_continue(state: ChatState) -> str:
        """Decide if conversation should continue."""
        if state["is_finished"] or state["turn_count"] >= MAX_CHAT_TURNS:
            return END
        return "target_agent_turn"
    
    def should_continue_from_target(state: ChatState) -> str:
        """Decide if conversation should continue from target agent turn."""
        if state["is_finished"] or state["turn_count"] >= MAX_CHAT_TURNS:
            return END
        return "main_agent_turn"
    
    graph = StateGraph(ChatState)
    graph.add_node("main_agent_turn", main_agent_turn)
    graph.add_node("target_agent_turn", target_agent_turn)    
    graph.add_edge(START, "main_agent_turn")
    graph.add_conditional_edges("main_agent_turn", should_continue, ["target_agent_turn", END])
    graph.add_conditional_edges("target_agent_turn", should_continue_from_target, ["main_agent_turn", END])
    return graph.compile()

@tool(args_schema=Decision)
def make_decision(decision: str, reason: str, config: RunnableConfig) -> dict:
    """Use this tool to make a final decision about the event and explain your reasoning."""

# TO BE INVOKED LIKE THIS: 
#     graph.invoke(
#     {"messages": [prompt]}, 
#     config={"configurable": {"agent_id": "ag174...", "event_id": "evt992..."}}
# )   
    agent_id = config.get("configurable", {}).get("agent_id")
    event_id = config.get("configurable", {}).get("event_id")
    
    if not agent_id or not event_id:
        return {"error": "Missing context (agent_id or event_id) in execution."}

    redis_client = initialize_redis()
    
    response_data = {
        "type": "decision",
        "agent_id": agent_id,
        "event_id": event_id,
        "decision": decision,
        "reason": reason
    }
    
    redis_client.rpush(f"simulation:event:{event_id}:actions", json.dumps(response_data))
    
    return {"status": "success", "message": "Successfully logged your decision."}

@tool(args_schema=SocialMediaPost)
def post_social_media(content: str, config: RunnableConfig) -> dict:
    """Use this tool to publish a social media post expressing your thoughts on the event."""
    agent_id = config.get("configurable", {}).get("agent_id")
    event_id = config.get("configurable", {}).get("event_id")
    
    if not agent_id or not event_id:
        return {"error": "Missing context."}
    
    redis_client = initialize_redis()
    response_data = {
        "type": "social_media_post",
        "agent_id": agent_id,
        "event_id": event_id,
        "content": content
    }
    redis_client.rpush(f"simulation:event:{event_id}:actions", json.dumps(response_data))
    return {"status": "success", "message": "Successfully posted to social media."}

@tool(args_schema=ChatWithAgent)
def chat_with_agent(target_agent_id: str, initial_intent: str, config: RunnableConfig) -> str:
    """Use this tool to have a multi-turn conversation with another agent about the event."""
    agent_id = config.get("configurable", {}).get("agent_id")
    event_id = config.get("configurable", {}).get("event_id")
    event_description = config.get("configurable", {}).get("event_description", "Unknown Event")
    
    if not agent_id or not event_id:
        return "Error: Missing context (agent_id or event_id)."
    
    redis_client = initialize_redis()

    agent_raw = redis_client.get(f"agent:{agent_id}")
    target_raw = redis_client.get(f"agent:{target_agent_id}")
    
    if not agent_raw or not target_raw:
        return "Error: One or both agents could not be found in the database."
    
    agent_data = json.loads(agent_raw)
    target_data = json.loads(target_raw)
    target_data["agent_id"] = target_agent_id  

    chat_graph = _build_chat_subgraph(
        agent_id=agent_id,
        agent_data=agent_data,
        target_data=target_data,
        event_id=event_id,
        event_description=event_description,
        initial_intent=initial_intent,
        redis_client=redis_client
    )
    
    initial_state = {
        "messages": [],
        "turn_count": 0,
        "is_finished": False
    }

    result = chat_graph.invoke(initial_state)
    agent_name = agent_data.get("name", agent_id)
    target_name = target_data.get("name", target_agent_id)
    
    conv_key = f"event:{event_id}:conv:{min(agent_id, target_agent_id)}_{max(agent_id, target_agent_id)}"
    for message in result["messages"]:
        redis_client.rpush(conv_key, message)

    interaction_data = {
        "type": "conversation",
        "agent_id": agent_id,
        "target_agent_id": target_agent_id,
        "event_id": event_id,
        "message_count": len(result["messages"]),
        "turn_count": result["turn_count"],
        "auto_ended": result["turn_count"] >= MAX_CHAT_TURNS
    }

    redis_client.rpush(f"simulation:event:{event_id}:interactions", json.dumps(interaction_data))
    transcript = "\n".join(result["messages"])
    
    return f"Conversation with {target_name} concluded after {result['turn_count']} turns:\n\n{transcript}"

