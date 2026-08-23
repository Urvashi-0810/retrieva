from fastapi import FastAPI, Depends, WebSocket
from fastapi.responses import StreamingResponse
import time

from app.pipeline.orchestrator import PipelineOrchestrator
from app.dependencies import get_orchestrator
from app.websocket.router import router as websocket_router

app = FastAPI(title="Voice-Enabled RAG API")
app.include_router(websocket_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
    
@app.post("/api/v1/query")
async def process_text_query(query: str, orchestrator: PipelineOrchestrator = Depends(get_orchestrator)):
    async def stream_generator():
        async for token in orchestrator.process_query(f"req_{int(time.time())}", query):
            yield token
            
    return StreamingResponse(stream_generator(), media_type="text/plain")
