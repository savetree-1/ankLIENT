from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class HistoryItem:
    id: Optional[int]
    timestamp: datetime
    prompt: str
    response: str
    category: Optional[str]
    ttft_ms: float
    total_ms: float
    word_count: int
    char_count: int
    status: str
