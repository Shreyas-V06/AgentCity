import uuid
from schemas.events import Event, EventList
from typing import List
from db import initialize_db

def generate_event_objects(event_list: EventList) -> List[Event]:
    """
    Generates a list of Event objects from a given list of EventBase objects.

    Args:
        event_list (List[EventBase]): A list of EventBase objects.

    Returns:
        List[Event]: A list of Event objects with unique event IDs.
    """
    events = []
    for event_base in event_list:
        event_id = f"evt{uuid.uuid4().int:016d}"
        event = Event(
            event_id=event_id,
            event_description=event_base.event_description,
            timeline=event_base.timeline,
            agent_id=event_base.agent_id
        )
        events.append(event)
    return events


def generate_agent_details_string(agent_ids: List[str]) -> str:
    """
    Fetches agent details from the database for the given list of agent_ids
    and returns them as a formatted string.
    """
    db = initialize_db()
    agents_collection = db['agents']
    
    # Fetch all agents matching the provided IDs
    agents_cursor = agents_collection.find({"agent_id": {"$in": agent_ids}})
    
    formatted_details = []
    
    for agent in agents_cursor:
        agent_str = f"Agent ID: {agent.get('agent_id')}\n"
        # Iterate over other fields, excluding _id and agent_id (already added)
        for key, value in agent.items():
            if key not in ['_id', 'agent_id']:
                agent_str += f"{key}: {value}\n"
        formatted_details.append(agent_str)
        
    return "\n" + "\n".join(formatted_details) + "\n" +  "\n"


