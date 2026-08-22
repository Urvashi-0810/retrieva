from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class EvidenceChunk(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    score: float
    rank: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RetrievalResult(BaseModel):
    chunks: List[EvidenceChunk]
    latency_ms: float
    confidence: float
    status: str
