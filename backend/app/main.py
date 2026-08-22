from fastapi import FastAPI, Depends, WebSocket
from fastapi.responses import StreamingResponse
import time

from app.core.config import settings
from app.pipeline.orchestrator import PipelineOrchestrator
from app.services.llm import GroqLLMService
from app.services.interfaces import (
    EmbeddingServiceProtocol, RetrievalServiceProtocol,
    CacheServiceProtocol, GuardrailServiceProtocol,
    TelemetryCollectorProtocol
)
from app.schemas.retrieval import RetrievalResult, EvidenceChunk
from app.schemas.telemetry import CacheResult, GuardrailResult

# --- STUBS FOR NOW ---
class StubEmbeddingService(EmbeddingServiceProtocol):
    async def embed_query(self, query: str) -> list[float]:
        return [0.0] * 768

class StubRetrievalService(RetrievalServiceProtocol):
    async def retrieve(self, query: str, query_embedding: list[float]) -> RetrievalResult:
        return RetrievalResult(
            chunks=[EvidenceChunk(chunk_id="1", document_id="doc1", text="This is a stub evidence chunk.", score=0.9, rank=1)],
            latency_ms=10.0,
            confidence=0.9,
            status="success"
        )

class StubCacheService(CacheServiceProtocol):
    async def get_cached_answer(self, query: str, query_embedding: list[float]) -> CacheResult:
        return CacheResult(hit=False, route="miss", latency_ms=1.0)
        
    async def set_cached_answer(self, query: str, query_embedding: list[float], answer: str, evidence_chunk_ids: list[str]):
        pass

class StubGuardrailService(GuardrailServiceProtocol):
    async def validate_query(self, query: str) -> GuardrailResult:
        return GuardrailResult(passed=True, outcome="pass", reason="", confidence=1.0, latency_ms=1.0)
        
    async def validate_retrieval(self, query: str, retrieval_result: RetrievalResult) -> GuardrailResult:
        return GuardrailResult(passed=True, outcome="pass", reason="", confidence=1.0, latency_ms=1.0)
        
    async def validate_grounding(self, query: str, answer: str, retrieval_result: RetrievalResult) -> GuardrailResult:
        return GuardrailResult(passed=True, outcome="pass", reason="", confidence=1.0, latency_ms=1.0)

class StubTelemetry(TelemetryCollectorProtocol):
    async def record_metric(self, request_id: str, metric_name: str, value: float):
        pass

# --- APP SETUP ---

def get_orchestrator() -> PipelineOrchestrator:
    llm = GroqLLMService(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None
    
    return PipelineOrchestrator(
        embedding_service=StubEmbeddingService(),
        retrieval_service=StubRetrievalService(),
        cache_service=StubCacheService(),
        guardrail_service=StubGuardrailService(),
        llm_service=llm,
        telemetry_collector=StubTelemetry()
    )

app = FastAPI(title="Voice-Enabled RAG API")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
    
@app.post("/api/v1/query")
async def process_text_query(query: str, orchestrator: PipelineOrchestrator = Depends(get_orchestrator)):
    async def stream_generator():
        async for token in orchestrator.process_query(f"req_{int(time.time())}", query):
            yield token
            
    return StreamingResponse(stream_generator(), media_type="text/plain")
