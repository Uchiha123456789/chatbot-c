from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class FeedbackUpsert(BaseModel):
    rating: Literal[-1, 1]
    comment: str | None = Field(default=None, max_length=1000)


class FeedbackOut(BaseModel):
    id: int
    message_id: int
    rating: int
    comment: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
