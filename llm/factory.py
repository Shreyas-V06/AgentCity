import os
from enum import Enum
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

class LLMProvider(str, Enum):
    OPENAI = "openai"

class LLMConfig(BaseModel):
    provider: LLMProvider = LLMProvider.OPENAI
    model_name: str = "gpt-5-nano"
    temperature: float = 0.7

class LLMFactory:    
    @staticmethod
    def build(config: LLMConfig):
        if config.provider == LLMProvider.OPENAI:
            return ChatOpenAI(
                model=config.model_name,
                temperature=config.temperature,
                api_key=os.getenv("OPENAI_API_KEY"),
                timeout=30.0
            )
        raise ValueError(f"Provider {config.provider} not supported.")

