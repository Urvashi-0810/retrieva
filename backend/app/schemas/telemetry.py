from pydantic import BaseModel, Field
from typing import List, Optional

class CacheResult(BaseModel):
    hit: bool
    route: str
    answer: Optional[str] = None
    evidence_chunk_ids: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    latency_ms: float

class GuardrailResult(BaseModel):
    passed: bool
    outcome: str
    reason: str
    confidence: float
    latency_ms: float

class PipelineMetrics(BaseModel):
    vad_ms: float = 0.0
    stt_ms: float = 0.0
    embedding_ms: float = 0.0
    cache_lookup_ms: float = 0.0
    retrieval_ms: float = 0.0
    guardrail_pre_ms: float = 0.0
    guardrail_post_ms: float = 0.0
    llm_ttft_ms: float = 0.0
    llm_generation_ms: float = 0.0
    rag_hot_path_ms: float = 0.0
    audio_to_first_response_ms: float = 0.0
    grounding_status: str = "unknown"
