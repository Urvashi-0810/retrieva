from typing import AsyncGenerator
from app.schemas.pipeline import PipelineState
from app.pipeline.state_machine import PipelineStateMachine
from app.schemas.retrieval import RetrievalResult
from app.services.interfaces import (
    EmbeddingServiceProtocol,
    RetrievalServiceProtocol,
    CacheServiceProtocol,
    GuardrailServiceProtocol,
    LLMServiceProtocol,
    TelemetryCollectorProtocol
)

class PipelineOrchestrator:
    def __init__(
        self,
        embedding_service: EmbeddingServiceProtocol,
        retrieval_service: RetrievalServiceProtocol,
        cache_service: CacheServiceProtocol,
        guardrail_service: GuardrailServiceProtocol,
        llm_service: LLMServiceProtocol,
        telemetry_collector: TelemetryCollectorProtocol
    ):
        self.embedding_service = embedding_service
        self.retrieval_service = retrieval_service
        self.cache_service = cache_service
        self.guardrail_service = guardrail_service
        self.llm_service = llm_service
        self.telemetry = telemetry_collector

    async def process_query(self, request_id: str, query: str) -> AsyncGenerator[str, None]:
        import time
        state_machine = PipelineStateMachine(PipelineState.QUERY_READY)
        
        try:
            # 1. Guardrail - validate query
            start = time.perf_counter_ns()
            query_guardrail = await self.guardrail_service.validate_query(query)
            await self.telemetry.record_metric(request_id, "guardrail_pre_ms", (time.perf_counter_ns() - start) / 1_000_000.0)
            await self.telemetry.record_metric(request_id, "guardrail_outcome", query_guardrail.outcome)
            
            if not query_guardrail.passed:
                state_machine.transition(PipelineState.CANCELLED)
                yield f"System: {query_guardrail.reason}"
                await self.telemetry.finalize_request(request_id)
                return
                
            # 2. L1 Cache Check
            state_machine.transition(PipelineState.CACHE_CHECK)
            start = time.perf_counter_ns()
            l1_result = await self.cache_service.get_exact_cached_answer(query)
            
            if l1_result.hit and l1_result.answer:
                await self.telemetry.record_metric(request_id, "cache_lookup_ms", (time.perf_counter_ns() - start) / 1_000_000.0)
                await self.telemetry.record_metric(request_id, "cache_status", "hit")
                state_machine.transition(PipelineState.CACHE_HIT)
                state_machine.transition(PipelineState.STREAMING)
                yield l1_result.answer
                state_machine.transition(PipelineState.GROUNDED)
                state_machine.transition(PipelineState.COMPLETED)
                await self.telemetry.finalize_request(request_id)
                return
                
            # 3. Embed Query (only on L1 miss)
            start_embed = time.perf_counter_ns()
            query_embedding = await self.embedding_service.embed_query(query)
            await self.telemetry.record_metric(request_id, "embedding_ms", (time.perf_counter_ns() - start_embed) / 1_000_000.0)
            
            # 4. L2 Semantic Cache Check
            l2_result = await self.cache_service.get_semantic_cached_answer(query_embedding)
            
            if l2_result.hit and l2_result.answer:
                await self.telemetry.record_metric(request_id, "cache_lookup_ms", (time.perf_counter_ns() - start) / 1_000_000.0)
                await self.telemetry.record_metric(request_id, "cache_status", "hit")
                state_machine.transition(PipelineState.CACHE_HIT)
                state_machine.transition(PipelineState.STREAMING)
                yield l2_result.answer
                state_machine.transition(PipelineState.GROUNDED)
                state_machine.transition(PipelineState.COMPLETED)
                await self.telemetry.finalize_request(request_id)
                return
                
            # Record total cache lookup time on miss
            await self.telemetry.record_metric(request_id, "cache_lookup_ms", (time.perf_counter_ns() - start) / 1_000_000.0)
            await self.telemetry.record_metric(request_id, "cache_status", "miss")
            
            # 5. Retrieval
            state_machine.transition(PipelineState.CACHE_MISS)
            state_machine.transition(PipelineState.RETRIEVING)
            
            start = time.perf_counter_ns()
            retrieval_result = await self.retrieval_service.retrieve(query, query_embedding)
            await self.telemetry.record_metric(request_id, "retrieval_ms", (time.perf_counter_ns() - start) / 1_000_000.0)
            
            # 6. Retrieval Validation
            retrieval_guardrail = await self.guardrail_service.validate_retrieval(query, retrieval_result)
            await self.telemetry.record_metric(request_id, "guardrail_outcome", retrieval_guardrail.outcome)
            if not retrieval_guardrail.passed:
                state_machine.transition(PipelineState.CANCELLED)
                yield f"System: {retrieval_guardrail.reason}"
                await self.telemetry.finalize_request(request_id)
                return
                
            state_machine.transition(PipelineState.RETRIEVAL_VALIDATED)
            
            # 7. Generation
            state_machine.transition(PipelineState.GENERATING)
            state_machine.transition(PipelineState.STREAMING)
            
            full_answer = ""
            start = time.perf_counter_ns()
            first_token_received = False
            
            if self.llm_service is not None:
                async for token in self.llm_service.generate_answer_stream(query, retrieval_result):
                    if not first_token_received:
                        await self.telemetry.record_metric(request_id, "llm_ttft_ms", (time.perf_counter_ns() - start) / 1_000_000.0)
                        first_token_received = True
                    full_answer += token
                    yield token
            else:
                await self.telemetry.record_metric(request_id, "llm_ttft_ms", 1.0)
                full_answer = "[Mock LLM Response based on context]"
                yield full_answer
                
            # 8. Post-generation Grounding Validation
            start = time.perf_counter_ns()
            grounding_guardrail = await self.guardrail_service.validate_grounding(query, full_answer, retrieval_result)
            await self.telemetry.record_metric(request_id, "guardrail_post_ms", (time.perf_counter_ns() - start) / 1_000_000.0)
            await self.telemetry.record_metric(request_id, "guardrail_outcome", grounding_guardrail.outcome)
            
            if grounding_guardrail.outcome == "pass":
                state_machine.transition(PipelineState.GROUNDED)
                # Cache the new safe answer
                evidence_ids = [chunk.chunk_id for chunk in retrieval_result.chunks]
                await self.cache_service.set_cached_answer(query, query_embedding, full_answer, evidence_ids)
                state_machine.transition(PipelineState.COMPLETED)
            elif grounding_guardrail.outcome == "regenerate":
                state_machine.transition(PipelineState.ERROR)
            else:
                state_machine.transition(PipelineState.CANCELLED)
            
            await self.telemetry.finalize_request(request_id)
            
        except Exception as e:
            state_machine.transition(PipelineState.ERROR)
            yield f"Error: {str(e)}"
            await self.telemetry.finalize_request(request_id)
