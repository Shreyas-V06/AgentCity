from pydantic import BaseModel, Field

class Decision(BaseModel):
    decision: str = Field(description="The decision made after evaluating an event or situation.")
    reason: str = Field(description="The rationale and thought process behind the decision.")

class SocialMediaPost(BaseModel):
    content: str = Field(description="The text content of the social media post.")



