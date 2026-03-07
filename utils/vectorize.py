from schemas.policy import PolicyWeight
from prompts import VECTORIZE_POLICY_PROMPT

def vectorize_policy(llm,policy:str):
    """
    Converts a policy into a vector.
    It uses an LLM for the same.
    """
    structured_llm = llm.with_structured_output(PolicyWeight)
    weight_obj = structured_llm.invoke(VECTORIZE_POLICY_PROMPT.format(policy=policy))
    weight = weight_obj.model_dump()
    return weight





