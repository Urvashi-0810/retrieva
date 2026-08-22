from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime

class WebSocketEvent(BaseModel):
    type: str
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]

class TranscriptEvent(BaseModel):
    request_id: str
    text: str
    is_final: bool
    stability: float

class LLMResultEvent(BaseModel):
    request_id: str
    full_text: str
    grounding_status: str
    evidence_chunk_ids: List[str]
    ttft_ms: float
    generation_ms: float
