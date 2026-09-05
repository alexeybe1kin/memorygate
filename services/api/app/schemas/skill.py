from pydantic import BaseModel, Field


class SkillWriteRequest(BaseModel):
    agent_id: str | None = None
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=12000)
    linked_tools: list[str] = Field(default_factory=list)
    version: str = Field(default="1", max_length=40)
    active: bool = True


class SkillPatchRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    body: str | None = Field(default=None, min_length=1, max_length=12000)
    linked_tools: list[str] | None = None
    version: str | None = Field(default=None, max_length=40)
    active: bool | None = None
