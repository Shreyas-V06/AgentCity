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
- A dimension should only have a high weight if the policy explicitly targets or significantly disrupts that area.
- Most policies are "narrow"; if a dimension is completely irrelevant, the valuemust be near 1.

# Constraints
1. Granularity: Avoid round numbers (e.g., 50, 60, 75). Provide high-precision, unique integers.
2. Range: 1-100.

# Policy
{policy_text}

"""