from typing import Dict, List
import numpy as np
import json 
from db import initialize_db

class ScreenConfig:
    """
    Sets up the configuration for screening agents
    """
    def __init__(self,policy_weight,population_size=25,profile_path=r"C:\Users\Shreyas\Desktop\AgentCity\agent_profiles.json"):
        self.policy_weight = policy_weight
        self.population_size = population_size
        self.profile_path = profile_path


class AgentScreener:
    """
    Sets up an AgentScreener with given configuration
    """
    def __init__(self, config: ScreenConfig):
        self.config = config

    def screen_agents(self) -> List[str]:
        with open(self.config.profile_path, 'r') as f:
            profiles = json.load(f)

        db = initialize_db()
        agents_collection = db['agents']
        if profiles:
            try:
                agents_collection.insert_many(profiles)
            except Exception as e:
                print(f"Error inserting agents into database: {e}")

        agent_ids = []
        weight_list = []

        for agent in profiles:
            agent_ids.append(agent['agent_id'])
            weight_list.append(list(agent['weights'].values()))

        weights_matrix = np.array(weight_list)
        policy_vec = np.array(list(self.config.policy_weight.values()))

        scores = np.dot(weights_matrix, policy_vec)

        k = min(self.config.population_size, len(scores))
        top_k_idx = np.argpartition(scores, -k)[-k:]
        sorted_indices = top_k_idx[np.argsort(scores[top_k_idx])[::-1]]

        return [agent_ids[i] for i in sorted_indices]


# EXAMPLE USAGE:
# config = ScreenConfig(policy_weight={'entertainment': 0.9, 'tax': 0.1, ...})
# screener = AgentScreener(config)
# top_agents = screener.screen_agents()