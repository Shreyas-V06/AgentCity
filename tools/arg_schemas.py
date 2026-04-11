from pydantic import BaseModel, Field

class Decision(BaseModel):
    decision: str = Field(description="The decision made after evaluating an event or situation.")
    reason: str = Field(description="The rationale and thought process behind the decision.")

class AgentMessage(BaseModel):
    target_agent_id: str = Field(description="The explicit agent_id of the relation you are messaging.")
    content: str = Field(description="The message needed to be transferred.")
    is_ready_to_exit: bool = Field(description="Set to true if your last message concluded the conversation.")


class SocialMediaPost(BaseModel):
    content: str = Field(description="The text content of the social media post.")



