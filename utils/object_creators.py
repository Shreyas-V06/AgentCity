from schemas.events import Event,EventBase
from typing import Literal

def generate_event_objects(event_base:EventBase,event_type:Literal['DIRECT','INDIRECT','INFLUENCED'],timeline:Literal['L1','L2','L3']):
    event_list = []
    for event in event_base:
        event_list.append(Event(event_description=event_base.event_description,event_type=event_type,timeline=timeline))
    return event_list


