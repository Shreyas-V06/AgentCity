import uuid
from schemas.events import Event, EventList
from typing import List
import json
from db import initialize_redis


def generate_event_objects(event_list: EventList) -> List[Event]:
    """
    Generates a list of Event objects from a given list of EventBase objects.

    Args:
        event_list (List[EventBase]): A list of EventBase objects.

    Returns:
        List[Event]: A list of Event objects with unique event IDs.
    """
    events = []
    for event_base in event_list.events:
        event_id = f"evt{uuid.uuid4().int:016d}"
        event = Event(
            event_id=event_id,
            event_description=[event_base.event_description],
            timeline=event_base.timeline,
            agent_id=event_base.agent_id
        )
        events.append(event)
    return events


def generate_agent_details_string(agent_ids: List[str]) -> str:
    """
    Fetches agent details from Redis for the given list of agent_ids
    and returns them as a formatted string.
    """
    redis_client = initialize_redis()

    keys = [f"agent:{agent_id}" for agent_id in agent_ids]
    raw_values = redis_client.mget(keys)

    formatted_details = []

    for raw in raw_values:
        if raw is None:
            continue
        agent = json.loads(raw)
        agent_str = f"Agent ID: {agent.get('agent_id')}\n"
        for key, value in agent.items():
            if key != 'agent_id':
                agent_str += f"{key}: {value}\n"
        formatted_details.append(agent_str)

    return "\n" + "\n".join(formatted_details) + "\n" + "\n"


def print_events(eventlist):
    """
    Print the events from EventList Object
    
    """
    print(f"Total Events: {len(eventlist)}\n")
    for i, event in enumerate(eventlist, 1):
        print(f"Event {i}:")
        print(f"  ID: {event.event_id}")
        print(f"  Agent ID: {event.agent_id}")
        print(f"  Timeline: {event.timeline}")
        desc = " ".join(event.event_description) if isinstance(event.event_description, list) else event.event_description
        print(f"  Description: {desc}")
        print("-" * 50)

def print_base_reactions(reactions):
    for i, r in enumerate(reactions, 1):
        print(f"--- Reaction {i} ---")
        print(f"Event ID : {r['event_id']}")
        print(f"Agent ID : {r['agent_id']}")
        print(f"Reaction : {r['base_reaction']}")
        print()

def generate_agent_data(agent_id: str) -> dict:
    """
    Fetches agent data as a dictionary from Redis for the given agent_id.
    """
    redis_client = initialize_redis()
    raw = redis_client.get(f"agent:{agent_id}")
    if raw:
        return json.loads(raw)
    return {}