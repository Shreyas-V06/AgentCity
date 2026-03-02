import os
from enum import Enum
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq


class LLMProvider(str, Enum):
    OPENAI = "openai"
    GOOGLE = "google"
    GROQ = "groq"

class LLMConfig(BaseModel):
    provider: LLMProvider
    model_name: str
    temperature: float

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
        elif config.provider == LLMProvider.GOOGLE:
            return ChatGoogleGenerativeAI(
                model=config.model_name,
                temperature=config.temperature,
                api_key=os.getenv("GOOGLE_API_KEY"),
                timeout=30.0
            )
        elif config.provider == LLMProvider.GROQ:
            return ChatGroq(
                model_name=config.model_name,
                temperature=config.temperature,
                api_key=os.getenv("GROQ_API_KEY"),
                timeout=30.0
            )
        else:
            raise ValueError(f"Provider {config.provider} not supported.")
        
#USAGE: 
# from llm.factory import LLMConfig,LLMFactory,LLMProvider
# config = LLMConfig(provider=LLMProvider.GROQ,model_name="llama-3.3-70b-versatile",temperature=0.5)
# llm = LLMFactory.build(config)
# llm.invoke("Hello, Which LLM are you?").content

