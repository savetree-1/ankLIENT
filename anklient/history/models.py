from dataclasses import dataclass
from datetime import datetime


@dataclass
class HistoryItem:
    id: int | None
    timestamp: datetime
    prompt: str
    response: str
    category: str | None
    ttft_ms: float
    total_ms: float
    word_count: int
    char_count: int
    status: str
