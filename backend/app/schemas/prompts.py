from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DraftCreateRequest(BaseModel):
    content: str = Field(min_length=1)
    variables_schema: dict[str, Any] | None = None
    created_by: str | None = None
    description: str | None = None
    owner_team: str | None = None


class PublishRequest(BaseModel):
    published_by: str | None = None


class RollbackRequest(BaseModel):
    to_version: int = Field(ge=1)
    published_by: str | None = None


class PromptVersionItem(BaseModel):
    id: int
    version: int
    status: str
    checksum: str
    content: str
    variables_schema: dict[str, Any] | None
    created_by: str | None
    created_at: datetime
    updated_at: datetime


class PromptSummary(BaseModel):
    prompt_key: str
    description: str | None
    owner_team: str | None
    updated_at: datetime
    active_version: int | None


class PromptDetail(BaseModel):
    prompt_key: str
    description: str | None
    owner_team: str | None
    active_version_id: int | None
    versions: list[PromptVersionItem]


class PublishResult(BaseModel):
    ok: bool
    prompt_key: str
    publish_event_id: int
    version: int
    environment: str
    deliveries_created: int


class PushDeliveryItem(BaseModel):
    id: int
    publish_event_id: int
    agent_id: int
    status: str
    attempt: int
    last_http_status: int | None
    last_error: str | None
    next_retry_at: datetime | None
    updated_at: datetime


class PublishEventItem(BaseModel):
    publish_event_id: int
    prompt_key: str
    version: int
    environment: str
    published_by: str | None
    published_at: datetime
    deliveries: list[PushDeliveryItem]


class WorkerRunResult(BaseModel):
    processed: int
    succeeded: int
    failed: int
    still_pending: int
