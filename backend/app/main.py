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

from app.services.cache import ExactL1Cache, SemanticL2Cache
from app.services.guardrails import GuardrailService, FALLBACK_MESSAGE
from app.telemetry.collector import TelemetryCollector

class ProductionCacheService(CacheServiceProtocol):
    def __init__(self):
        self.l1 = ExactL1Cache()
        self.l2 = SemanticL2Cache()
        
    async def get_exact_cached_answer(self, query: str) -> CacheResult:
        res = self.l1.get(query)
        if res:
            return CacheResult(hit=res["hit"], route=res["route"], answer=res["answer_text"], evidence_chunk_ids=res["evidence_chunk_ids"], confidence=res["retrieval_confidence"], latency_ms=res["latency_ms"])
        return CacheResult(hit=False, route="l1_exact", latency_ms=1.0)
        
    async def get_semantic_cached_answer(self, query_embedding: list[float]) -> CacheResult:
        res = self.l2.get(query_embedding)
        if res:
            return CacheResult(hit=res["hit"], route=res["route"], answer=res["answer_text"], evidence_chunk_ids=res["evidence_chunk_ids"], confidence=res["retrieval_confidence"], latency_ms=res["latency_ms"])
        return CacheResult(hit=False, route="l2_semantic", latency_ms=1.0)
        
    async def set_cached_answer(self, query: str, query_embedding: list[float], answer: str, evidence_chunk_ids: list[str]):
        try:
            self.l1.put(query, answer, evidence_chunk_ids, 1.0, "grounded")
            self.l2.put(query, query_embedding, answer, evidence_chunk_ids, 1.0, "grounded")
        except ValueError:
            pass

class ProductionGuardrailService(GuardrailServiceProtocol):
    def __init__(self):
        self.guardrails = GuardrailService()
        
    async def validate_query(self, query: str) -> GuardrailResult:
        res = self.guardrails.validate_query(query)
        reason = FALLBACK_MESSAGE if res["outcome"] == "abstain" else (res.get("reason") or "")
        return GuardrailResult(passed=res["passed"], outcome=res["outcome"], reason=reason, confidence=res["confidence"], latency_ms=res["latency_ms"])
        
    async def validate_retrieval(self, query: str, retrieval_result: RetrievalResult) -> GuardrailResult:
        res = self.guardrails.validate_retrieval(retrieval_result.confidence, len(retrieval_result.chunks))
        reason = FALLBACK_MESSAGE if res["outcome"] == "abstain" else (res.get("reason") or "")
        return GuardrailResult(passed=res["passed"], outcome=res["outcome"], reason=reason, confidence=res["confidence"], latency_ms=res["latency_ms"])
        
    async def validate_grounding(self, query: str, answer: str, retrieval_result: RetrievalResult) -> GuardrailResult:
        evidence_texts = [c.text for c in retrieval_result.chunks]
        res = self.guardrails.validate_grounding(answer, evidence_texts)
        reason = FALLBACK_MESSAGE if res["outcome"] == "abstain" else (res.get("reason") or "")
        return GuardrailResult(passed=res["passed"], outcome=res["outcome"], reason=reason, confidence=res["confidence"], latency_ms=res["latency_ms"])

class ProductionTelemetryAdapter(TelemetryCollectorProtocol):
    def __init__(self, collector: TelemetryCollector):
        self.collector = collector
        self.current_requests = {}
        
    async def record_metric(self, request_id: str, metric_name: str, value: float):
        if request_id not in self.current_requests:
            self.current_requests[request_id] = {"request_id": request_id}
        self.current_requests[request_id][metric_name] = value
        
    async def finalize_request(self, request_id: str):
        if request_id in self.current_requests:
            record = self.current_requests.pop(request_id)
            self.collector.add_record(record)

# --- APP SETUP ---

global_telemetry_collector = TelemetryCollector()
global_cache_service = ProductionCacheService()
global_guardrail_service = ProductionGuardrailService()
global_telemetry_adapter = ProductionTelemetryAdapter(global_telemetry_collector)

def get_orchestrator() -> PipelineOrchestrator:
    llm = GroqLLMService(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None
    
    return PipelineOrchestrator(
        embedding_service=StubEmbeddingService(),
        retrieval_service=StubRetrievalService(),
        cache_service=global_cache_service,
        guardrail_service=global_guardrail_service,
        llm_service=llm,
        telemetry_collector=global_telemetry_adapter
    )

app = FastAPI(title="Voice-Enabled RAG API")

from app.api.analytics import router as analytics_router
app.include_router(analytics_router)

from app.api.benchmark import router as benchmark_router
app.include_router(benchmark_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
    
@app.post("/api/v1/query")
async def process_text_query(query: str, orchestrator: PipelineOrchestrator = Depends(get_orchestrator)):
    async def stream_generator():
        async for token in orchestrator.process_query(f"req_{int(time.time())}", query):
            yield token
            
    return StreamingResponse(stream_generator(), media_type="text/plain")
