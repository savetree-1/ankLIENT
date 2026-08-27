from dataclasses import dataclass, field
from typing import Optional

@dataclass
class TimingMetrics:
    ttft_ms: float = 0.0
    total_ms: float = 0.0

@dataclass
class ChatResponse:
    content: str
    timing: TimingMetrics
    word_count: int
    char_count: int
    saved_images: list[str] = field(default_factory=list)
