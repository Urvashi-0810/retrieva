import uuid
import asyncio
from app.pipeline.orchestrator import PipelineOrchestrator
from app.telemetry.collector import TelemetryCollector
from app.main import (
    ProductionTelemetryAdapter,
    ProductionCacheService,
    ProductionGuardrailService,
    StubEmbeddingService,
    StubRetrievalService
)
from app.core.config import settings
from app.services.llm import GroqLLMService

async def run_benchmark(
    queries: list[str] | None = None,
    embedding_service=None,
    retrieval_service=None,
    llm_service=None
) -> dict:
    if not queries:
        queries = [
            "What are the benefits of vector databases?",
            "How does LLM retrieval work?"
        ]

    # Create isolated telemetry environment
    benchmark_collector = TelemetryCollector()
    benchmark_adapter = ProductionTelemetryAdapter(benchmark_collector)
    
    # Create isolated cache and guardrails
    benchmark_cache = ProductionCacheService()
    benchmark_guardrails = ProductionGuardrailService()

    # Use injected services or fallback to stubs/defaults
    emb_svc = embedding_service or StubEmbeddingService()
    ret_svc = retrieval_service or StubRetrievalService()
    
    if llm_service is not None:
        llm = llm_service
    else:
        llm = GroqLLMService(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None

    # Create isolated orchestrator
    orchestrator = PipelineOrchestrator(
        embedding_service=emb_svc,
        retrieval_service=ret_svc,
        cache_service=benchmark_cache,
        guardrail_service=benchmark_guardrails,
        llm_service=llm,
        telemetry_collector=benchmark_adapter
    )

    # Execute benchmark queries (Cold start then Warm start)
    run_queries = []
    for q in queries:
        run_queries.append(q) # Cold start
        run_queries.append(q) # Warm start

    for query in run_queries:
        req_id = f"bench_{uuid.uuid4().hex[:8]}"
        async for _ in orchestrator.process_query(req_id, query):
            pass # fully consume generator

    # Read snapshot
    snapshot = benchmark_collector.get_snapshot()
    
    cache_hit_count = sum(1 for req in snapshot if req.get("cache_status") == "hit")
    cache_miss_count = sum(1 for req in snapshot if req.get("cache_status") == "miss")
    
    percentiles = benchmark_collector.get_percentiles()
    
    return {
        "scenario_count": len(queries) * 2,
        "request_count": len(snapshot),
        "records": snapshot,
        "rag_hot_path": percentiles.get("rag_hot_path", {}),
        "audio_to_first_response": percentiles.get("audio_to_first_response", {}),
        "cache_hit_count": cache_hit_count,
        "cache_miss_count": cache_miss_count
    }
