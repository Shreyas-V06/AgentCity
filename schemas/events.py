from pydantic import BaseModel,Field
from typing import Literal,List

class Event:
    """
    Represents a specific simulation moment where a policy impacts a citizen.
    
    Fields:
    - event_description: A second-person narrative moment of the situation agent is part of(e.g., 'You are standing at the bus stop...')

    - event_type: 
        - 'DIRECT': Direct policy impact on the agent.
        - 'INDIRECT': Secondary effects (e.g., family/friends affected).
        - 'INFLUENCED': Changes in social opinion or community "vibe".
    
    - timeline: 
        - 'L1': Immediate (1 Week - 1 Month).
        - 'L2': Intermediate (1 Year).
        - 'L3': Long-term / Generational (3 Years+).
    """
    event_description: str
    event_type: Literal['DIRECT', 'INDIRECT', 'INFLUENCED']
    timeline: Literal['L1', 'L2', 'L3']

    def __init__(
        self, 
        event_description: str, 
        event_type: Literal['DIRECT', 'INDIRECT', 'INFLUENCED'], 
        timeline: Literal['L1', 'L2', 'L3']
    ):
        self.event_description = event_description
        self.event_type = event_type
        self.timeline = timeline


class EventBase(BaseModel):

    event_description: List[str] = Field(
        ...,
        description=(
            "A list of vivid, second-person 'Moments' representing a direct and highly probable consequence of the "
            "implemented policy. It must be an immediate, lived experience "
            "rather than a general opinion. The moment must be the most likely scenario "
            "faced by the specific agents involved, providing clear emotional and situational data "
            "for the sentiment evaluator to calculate state shifts."
            "Each moment should be a separate string object"
        )
    )

