import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PromptItem:
    prompt_key: str
    version: int
    checksum: str
    content: str
    variables_schema: dict[str, Any] | None
    updated_at: datetime


class PromptStore:
    def __init__(self, yaml_dir: str | None = None) -> None:
        self.cache: dict[str, PromptItem] = {}
        self.idempotency_seen: set[str] = set()
        target_dir = yaml_dir or os.getenv("PROMPT_YAML_DIR", "./data/prompts")
        self.yaml_dir = Path(target_dir)
        self.yaml_dir.mkdir(parents=True, exist_ok=True)

    def set_yaml_dir(self, yaml_dir: str) -> None:
        self.yaml_dir = Path(yaml_dir)
        self.yaml_dir.mkdir(parents=True, exist_ok=True)

    def upsert(
        self,
        prompt_key: str,
        version: int,
        checksum: str,
        content: str,
        variables_schema: dict[str, Any] | None,
    ) -> None:
        self.cache[prompt_key] = PromptItem(
            prompt_key=prompt_key,
            version=version,
            checksum=checksum,
            content=content,
            variables_schema=variables_schema,
            updated_at=datetime.now(timezone.utc),
        )

    def _file_path(self, prompt_key: str) -> Path:
        safe_key = prompt_key.replace("/", "__")
        return self.yaml_dir / f"{safe_key}.yml"

    def write_prompt_yaml(
        self,
        prompt_key: str,
        version: int,
        checksum: str,
        content: str,
        variables_schema: dict[str, Any] | None,
    ) -> Path:
        path = self._file_path(prompt_key)
        doc = {
            "prompt_key": prompt_key,
            "version": version,
            "checksum": checksum,
            "content": content,
            "variables_schema": variables_schema,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
        return path

    def load_prompt_yaml_file(self, path: Path) -> PromptItem:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        required = ["prompt_key", "version", "checksum", "content"]
        for key in required:
            if key not in data:
                raise ValueError(f"Missing required key in YAML: {key}")

        item = PromptItem(
            prompt_key=str(data["prompt_key"]),
            version=int(data["version"]),
            checksum=str(data["checksum"]),
            content=str(data["content"]),
            variables_schema=data.get("variables_schema"),
            updated_at=datetime.now(timezone.utc),
        )
        self.cache[item.prompt_key] = item
        return item

    def load_all_from_yaml(self) -> int:
        loaded = 0
        for path in self.yaml_dir.glob("*.yml"):
            self.load_prompt_yaml_file(path)
            loaded += 1
        return loaded

    def get(self, prompt_key: str) -> PromptItem:
        item = self.cache.get(prompt_key)
        if item is None:
            raise KeyError(f"Prompt not found: {prompt_key}")
        return item


prompt_store = PromptStore()
