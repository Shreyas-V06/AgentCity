import json
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from db import initialize_redis
from tools.arg_schemas import Decision, SocialMediaPost

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

