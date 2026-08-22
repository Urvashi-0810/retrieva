import os
from groq import AsyncGroq
from typing import AsyncGenerator
from app.schemas.retrieval import RetrievalResult
from app.services.interfaces import LLMServiceProtocol

class GroqLLMService(LLMServiceProtocol):
    def __init__(self, api_key: str, model: str = "openai/gpt-oss-20b"):
        self.client = AsyncGroq(api_key=api_key)
        self.model = model

    async def generate_answer_stream(self, query: str, retrieval_result: RetrievalResult) -> AsyncGenerator[str, None]:
        # Build prompt
        context_text = "\n\n".join([f"[{i+1}] {chunk.text}" for i, chunk in enumerate(retrieval_result.chunks)])
        
        system_prompt = (
            "You are a helpful assistant. Answer the user's question based strictly on the following context.\n"
            "If the context does not contain sufficient information to answer, state that clearly.\n\n"
            f"Context:\n{context_text}"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
