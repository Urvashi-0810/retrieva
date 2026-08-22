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
        state_machine = PipelineStateMachine(PipelineState.QUERY_READY)
        
        try:
            # 1. Guardrail - validate query
            query_guardrail = await self.guardrail_service.validate_query(query)
            if not query_guardrail.passed:
                state_machine.transition(PipelineState.COMPLETED)
                yield f"System: {query_guardrail.reason}"
                return
                
            # 2. Embed Query
            query_embedding = await self.embedding_service.embed_query(query)
            
            # 3. Cache Check
            state_machine.transition(PipelineState.CACHE_CHECK)
            cache_result = await self.cache_service.get_cached_answer(query, query_embedding)
            
            if cache_result.hit and cache_result.answer:
                state_machine.transition(PipelineState.CACHE_HIT)
                state_machine.transition(PipelineState.STREAMING)
                yield cache_result.answer
                state_machine.transition(PipelineState.COMPLETED)
                return
                
            # 4. Retrieval
            state_machine.transition(PipelineState.CACHE_MISS)
            state_machine.transition(PipelineState.RETRIEVING)
            
            retrieval_result = await self.retrieval_service.retrieve(query, query_embedding)
            
            # 5. Retrieval Validation
            retrieval_guardrail = await self.guardrail_service.validate_retrieval(query, retrieval_result)
            if not retrieval_guardrail.passed:
                state_machine.transition(PipelineState.COMPLETED)
                yield f"System: {retrieval_guardrail.reason}"
                return
                
            state_machine.transition(PipelineState.RETRIEVAL_VALIDATED)
            
            # 6. Generation
            state_machine.transition(PipelineState.GENERATING)
            state_machine.transition(PipelineState.STREAMING)
            
            full_answer = ""
            if self.llm_service is not None:
                async for token in self.llm_service.generate_answer_stream(query, retrieval_result):
                    full_answer += token
                    yield token
            else:
                full_answer = "[Mock LLM Response based on context]"
                yield full_answer
                
            state_machine.transition(PipelineState.GROUNDED)
            
            # Cache the new answer
            evidence_ids = [chunk.chunk_id for chunk in retrieval_result.chunks]
            await self.cache_service.set_cached_answer(query, query_embedding, full_answer, evidence_ids)
            
            state_machine.transition(PipelineState.COMPLETED)
            
        except Exception as e:
            state_machine.transition(PipelineState.ERROR)
            yield f"Error: {str(e)}"
