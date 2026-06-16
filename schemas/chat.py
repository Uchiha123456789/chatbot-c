from datetime import datetime

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class ConversationUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    is_archived: bool | None = None


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    is_archived: bool

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AskRequest(BaseModel):
    conversation_id: int
    question: str = Field(min_length=1, max_length=2000)


class AskResponse(BaseModel):
    answer: str
    user_message_id: int
    assistant_message_id: int
    retrieved_chunk_ids: list[str]
