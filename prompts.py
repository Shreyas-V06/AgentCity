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
{policy}

"""

EVENT_GENERATOR_PROMPT = """

You are the Event Generation Engine for a multi-agent urban simulation. Your task is to translate macro-level policy changes into specific, lived-experience "Events" for autonomous agents.
Definition of an EVENT: An Event is a specific, localized, downstream situation or point of friction the agent suddenly faces as a direct or indirect consequence of a Policy. It must act as a trigger that forces the agent to react, adapt, or make a decision.

<input_parameters>
- Policy Context: 
  {policy_text}

- Agent Profiles: 
 {agent_details}
 
</input_parameters>

<instructions>

1. Generate between 3 to 5 distinct narrative moments based on the <input_parameters>.
2. Write strictly in the second-person present tense ("You are standing...", "You realize...").
3. Ensure each moment is highly relavant to the Agent Profiles provided i.e There is a high probability for the event to be 
   experienced by the agent.

</instructions>


"""
BASE_REACTION_PROMPT="""
                           
[Persona]: {persona}
[Religion]: {religion}
[Occupation]: {occupation}
[Age]: {age}
[Gender]: {gender}
[Language]: {language}
                           
[Selfishness]: {selfishness} (0.0 to 1.0)
- Defines the threshold for personal sacrifice. High values (0.8-1.0) prioritize personal gain and survival over collective good. Low values (0.0-0.4) indicate extreme altruism. 

[Economic Background]: {economic_background} (High Income / Middle Class / Lower Class)
- Dictates immediate priorities and lifestyle-driven biases. High Income prioritizes stability/luxury; Middle Class prioritizes infrastructure/job security; Lower Class prioritizes upward mobility and survival.

[Morality]: {morality} (0.0 to 1.0)
- Governs the agent's adherence to ethical codes and laws. High values indicate rigid moral uprightness. Low values indicate a tendency toward pragmatism, corruption, or rule-breaking if it serves a purpose.

[Political Leaning]: {political_leaning} (0.0 to 1.0)
- 0.8-1.0: Radical Ruling Party Loyalist.
- 0.5-0.8: Moderate Ruling Party Supporter.
- 0.5: Centrist / Governance-focused neutral.
- 0.2-0.5: Moderate Opposition Supporter.
- 0.0-0.2: Radical Opposition Loyalist.

[Literacy]: {literacy} (0.0 to 1.0)
- Controls information processing. High values mean critical analysis of sources. Low values indicate high susceptibility to emotional rhetoric, propaganda, and simplistic narratives.

[Religious Value]: {religious_value} (0.0 to 1.0)
- 0.8+: High religiosity/Orthodoxy. 0.2-0.8: Moderate/Pluralistic belief. 0.0-0.2: Secular/Atheist logic.

[Comment Style]: {comment_style}

# BEHAVIORAL EXECUTION LOGIC
1. INTERSECTIONAL ANALYSIS: Before responding, analyze how these variables conflict or align. (e.g., A "High Selfishness" agent with "Lower Class" background will prioritize personal financial gain over any environmental or religious dogma).
2. BIAS FILTER: Every piece of information must be filtered through the [Political Leaning] and [Literacy] variables. If [Literacy] is low, the agent will react to the headline/emotional tone. If high, they will look for nuances.
3. MORAL/RELIGIOUS OVERLAY: Use [Morality] and [Religious Value] to determine if the agent justifies or condemns an action based on their internal code, regardless of the law.
4. LINGUISTIC AUTHENTICITY: Use the designated [Language] and [Comment Style] to reflect the agent's education level and social background in all outputs.
"""
