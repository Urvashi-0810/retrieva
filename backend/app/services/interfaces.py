from typing import Protocol, List, Optional, AsyncGenerator
from app.schemas.retrieval import RetrievalResult
from app.schemas.telemetry import CacheResult, GuardrailResult

class EmbeddingServiceProtocol(Protocol):
    async def embed_query(self, query: str) -> List[float]:
        ...

class RetrievalServiceProtocol(Protocol):
    async def retrieve(self, query: str, query_embedding: List[float]) -> RetrievalResult:
        ...

class CacheServiceProtocol(Protocol):
    async def get_exact_cached_answer(self, query: str) -> CacheResult:
        ...
        
    async def get_semantic_cached_answer(self, query_embedding: List[float]) -> CacheResult:
        ...
        
    async def set_cached_answer(self, query: str, query_embedding: List[float], answer: str, evidence_chunk_ids: List[str]):
        ...

class GuardrailServiceProtocol(Protocol):
    async def validate_query(self, query: str) -> GuardrailResult:
        ...
        
    async def validate_retrieval(self, query: str, retrieval_result: RetrievalResult) -> GuardrailResult:
        ...
        
    async def validate_grounding(self, query: str, answer: str, retrieval_result: RetrievalResult) -> GuardrailResult:
        ...

class LLMServiceProtocol(Protocol):
    async def generate_answer_stream(self, query: str, retrieval_result: RetrievalResult) -> AsyncGenerator[str, None]:
        ...

class VADServiceProtocol(Protocol):
    async def process_audio_frame(self, frame: bytes) -> bool:
        ...

class STTServiceProtocol(Protocol):
    async def transcribe(self, audio_data: bytes) -> str:
        ...

class TelemetryCollectorProtocol(Protocol):
    async def record_metric(self, request_id: str, metric_name: str, value: float):
        ...
        
    async def finalize_request(self, request_id: str):
        ...
