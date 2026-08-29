from dataclasses import dataclass
from datetime import datetime


@dataclass
class PromptModel:
    id: int | None
    name: str
    description: str
    category: str
    template: str
    tags: str
    favorite: bool
    usage_count: int
    last_used: datetime | None

    def get_tags(self) -> list[str]:
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",")]
