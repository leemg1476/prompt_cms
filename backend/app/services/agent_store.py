from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class CachedPrompt:
    prompt_key: str
    version: int
    checksum: str
    content: str
    variables_schema: dict[str, Any] | None
    updated_at: datetime


class PromptStore:
    def __init__(self) -> None:
        self.cache: dict[str, CachedPrompt] = {}

    def upsert(
        self,
        prompt_key: str,
        version: int,
        checksum: str,
        content: str,
        variables_schema: dict[str, Any] | None,
    ) -> None:
        self.cache[prompt_key] = CachedPrompt(
            prompt_key=prompt_key,
            version=version,
            checksum=checksum,
            content=content,
            variables_schema=variables_schema,
            updated_at=datetime.now(timezone.utc),
        )

    def get(self, prompt_key: str) -> CachedPrompt | None:
        return self.cache.get(prompt_key)


prompt_store = PromptStore()
