from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class PromptModel:
    id: Optional[int]
    name: str
    description: str
    category: str
    template: str
    tags: str
    favorite: bool
    usage_count: int
    last_used: Optional[datetime]

    def get_tags(self) -> List[str]:
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",")]
