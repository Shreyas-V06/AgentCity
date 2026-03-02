VECTORIZE_POLICY_PROMPT = """

# Role
Analyze the provided policy text and decompose its nature into a multi-dimensional impact vector.

# Dimensions
- Economy: tax (direct levies), cost_of_living (consumer prices), employment (job market), wealth (assets/capital).
- City: transport (mobility/transit), internet (digital infrastructure), safety (security/emergency), environment (ecology/parks).
- Human: education (learning/training), health (well-being/care), leisure (recreation/culture), welfare (social safety nets).
- Social: social_affinity (inter-agent relationships), civic_engagement (participation/trust).

# Task
Evaluate the "Intent" and "Inherent Impact" of the policy for each dimension. 
- A dimension should only have a high weight if the policy is relevant to that dimension or significantly disrupts that area.
- if a dimension is completely irrelevant, the value must be near 0.000.
- if a dimension is relevant , the value must be near 1.000

# Constraints
1. Provide high-precision, unique float values with atleast three significant digits after decimal point. (eg. 0.312 , 0.411)
2. Range: 0 to 1.

# Policy
{policy_text}

"""

EVENT_GENERATOR_PROMPT = """

# Role
You are an expert policy impact simulator. Generate vivid, second-person narrative moments that capture the real-world consequences of a policy.

# Task
Generate a list of specific, lived-experience events that represent how the policy impacts agents with the following characteristics:
- Event Type: {event_type} (DIRECT impact, INDIRECT effects, or INFLUENCED perspectives)
- Timeline: {timeline} (L1: immediate 1 week-1 month, L2: intermediate 1 year, L3: long-term 3+ years)

# Agent Details
{agent_details}

# Requirements
1. Each moment must be a concrete, vivid scenario written in second-person ("You are standing at...", "You receive a notice...").
2. Moments must reflect the most likely real-world experiences for the target demographic.
3. Ensure each moment is distinct and captures different facets of the policy impact.
4. Return between 3-5 distinct moments and must be a seperate string

# Policy Context
{policy_text}

"""

