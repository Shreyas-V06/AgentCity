from pydantic import BaseModel,Field
from typing import Literal,List,Union

class Event:
    """
    Represents a specific simulation moment where a policy impacts a citizen.

    Fields:
    - event_id: A unique identifier for the event.
    - event_description: A second-person narrative moment of the situation agent is part of (e.g., 'You are standing at the bus stop...').
    - timeline: Specifies the time frame in which the event's impact is observed.
    - agent_id: A unique identifier for the agent experiencing the event, linking the event to a specific agent profile.
    """
    event_id: str
    event_description: Union[str, List[str]]
    timeline: Literal['L1', 'L2', 'L3']
    agent_id: str

    def __init__(
        self,
        event_id: str,
        event_description: Union[str, List[str]],
        timeline: Literal['L1', 'L2', 'L3'],
        agent_id: str
    ):
        self.event_id = event_id
        self.event_description = event_description
        self.timeline = timeline
        self.agent_id = agent_id



class EventBase(BaseModel):
    """
    Represents a specific simulation moment where a policy impacts a citizen.

    Fields:
    - event_description: A second-person narrative moment of the situation agent is part of(e.g., 'You are standing at the bus stop...')

    - timeline: 
        - 'L1': Immediate (1 Week - 1 Month).
        - 'L2': Intermediate (1 Year).
        - 'L3': Long-term / Generational (3 Years+).
        Description: Specifies the time frame in which the event's impact is observed.

    - agent_id: A unique identifier for the agent experiencing the event, linking the event to a specific agent profile.
    """
    
    event_description: Union[str, List[str]] = Field(
        ...,
        description=(
            "A vivid, second-person 'event' representing a direct and highly probable consequence of the "
            "implemented policy. It must be an immediate, lived experience "
            "rather than a general opinion. The moment must be the most likely scenario "
            "faced by the specific agents involved, providing clear emotional and situational data "
            "for the sentiment evaluator to calculate state shifts."
        )
    )
    timeline: Literal['L1', 'L2', 'L3'] = Field(
        ...,
        description="Specifies the time frame in which the event's impact is observed."
    )
    agent_id: str = Field(
        ...,
        description="A unique identifier for the agent experiencing the event, linking the event to a specific agent profile."
    )


class EventList(BaseModel):
    """
    Represents a collection of EventBase objects.

    Fields:
    - events: A list of EventBase objects.
    """
    events: List[EventBase] = Field(
        default_factory=list,
        description="A list of EventBase objects representing multiple simulation moments."
    )

