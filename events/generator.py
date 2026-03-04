from typing import List
from schemas.events import Event, EventList
from utils.general import generate_event_objects
from llm.factory import LLMConfig, LLMFactory, LLMProvider
from prompts import EVENT_GENERATOR_PROMPT

#TODO:Create a proper abstraction for event generator which calls create_event_object in batches

def create_event_objects(policy_text: str, agent_details: str) -> List[Event]:
    """
    Generate Event objects based on a policy using structured output.
    
    Args:
        policy_text: The policy text to analyze for event generation
        event_type: Type of event - 'DIRECT', 'INDIRECT', or 'INFLUENCED'
        timeline: Timeline scope - 'L1' (1 week-1 month), 'L2' (1 year), or 'L3' (3+ years)
        agent_details: Details about the agents affected by the policy
    
    Returns:
        A list of Event objects representing the policy's impact moments

    NOTE: this method is supposed to be called in batches of agents, for token efficiency
    """

    #LLM for event creation 
    config = LLMConfig(
        provider=LLMProvider.GROQ,
        model_name="llama-3.3-70b-versatile",
        temperature=0.7
    )
    llm = LLMFactory.build(config)

    structured_llm = llm.with_structured_output(EventList)
    formatted_prompt = EVENT_GENERATOR_PROMPT.format(
        agent_details=agent_details,
        policy_text=policy_text
    )
    event_list = structured_llm.invoke(formatted_prompt)
    events = generate_event_objects(
        event_list=event_list
    )
    
    return events
