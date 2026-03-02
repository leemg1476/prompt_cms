from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PushPayload(BaseModel):
    prompt_key: str = Field(min_length=1)
    version: int = Field(ge=1)
    checksum: str = Field(min_length=1)
    content: str = Field(min_length=1)
    variables_schema: dict[str, Any] | None = None
    published_at: datetime | None = None


class PushApplyResponse(BaseModel):
    ok: bool
    prompt_key: str
    version: int
    applied: bool
    cache_state: str
