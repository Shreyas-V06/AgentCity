from pydantic import BaseModel

class PolicyWeight(BaseModel):
    """
    Schema representing the magnitude of a policy across 
    economic, city-wide, human, and social dimensions.
    """
    # Economy Cluster
    tax: float = 0.0
    cost_of_living: float = 0.0
    employment: float = 0.0
    wealth: float = 0.0

    # City Cluster
    transport: float = 0.0
    internet: float = 0.0
    safety: float = 0.0
    environment: float = 0.0

    # Human Cluster
    education: float = 0.0
    health: float = 0.0
    leisure: float = 0.0
    welfare: float = 0.0

    # Social Cluster
    social_affinity: float = 0.0
    civic_engagement: float = 0.0