from llm.factory import LLMConfig,LLMFactory,LLMProvider
from schemas.policy import PolicyWeight
from prompts import VECTORIZE_POLICY_PROMPT

def vectorize_policy(llm,policy:str):
    config = LLMConfig(LLMProvider.OPENAI,model_name="gpt-5-nano")
    llm = LLMFactory.build(config)
    structured_llm = llm.with_structured_output(PolicyWeight)
    weight = structured_llm.invoke(VECTORIZE_POLICY_PROMPT.format(policy))
    return weight



