from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256


@dataclass
class PromptVersion:
    id: str
    agent_id: str
    content: str
    version: int
    locked: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PromptRegistry:
    def __init__(self):
        self._items: dict[str, list[PromptVersion]] = {}

    def create(self, agent_id: str, content: str) -> PromptVersion:
        versions = self._items.setdefault(agent_id, [])
        item = PromptVersion(
            id=sha256(f"{agent_id}:{len(versions)+1}:{content}".encode()).hexdigest()[:16],
            agent_id=agent_id,
            content=content,
            version=len(versions) + 1,
        )
        versions.append(item)
        return item

    def list(self, agent_id: str) -> list[PromptVersion]:
        return list(self._items.get(agent_id, []))

    def lock(self, agent_id: str, version: int) -> PromptVersion:
        for item in self._items.get(agent_id, []):
            if item.version == version:
                item.locked = True
                return item
        raise KeyError((agent_id, version))
