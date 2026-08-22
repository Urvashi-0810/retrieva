from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from app.main import global_telemetry_collector

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

def get_summary_payload():
    snapshot = global_telemetry_collector.get_snapshot()
    total_count = len(snapshot)
    
    # Calculate Cache Hit Rate
    cache_hits = sum(1 for req in snapshot if req.get("cache_status") == "hit")
    cache_hit_rate = (cache_hits / total_count) if total_count > 0 else 0.0
    
    # Calculate Guardrail Abstain Rate
    guardrail_abstains = sum(1 for req in snapshot if req.get("guardrail_outcome") == "abstain")
    guardrail_abstain_rate = (guardrail_abstains / total_count) if total_count > 0 else 0.0
    
    percentiles = global_telemetry_collector.get_percentiles()
    
    return {
        "request_count": total_count,
        "rag_hot_path": percentiles.get("rag_hot_path", {}),
        "audio_to_first_response": percentiles.get("audio_to_first_response", {}),
        "cache_hit_rate": cache_hit_rate,
        "guardrail_abstain_rate": guardrail_abstain_rate
    }

@router.get("/summary")
async def get_analytics_summary():
    return get_summary_payload()

class TelemetryBroadcaster:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.is_running = False
        self._task = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        if not self.is_running:
            self.start()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if not self.active_connections:
            self.stop()

    def start(self):
        self.is_running = True
        self._task = asyncio.create_task(self._broadcast_loop())

    def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _broadcast_loop(self):
        try:
            while self.is_running:
                if self.active_connections:
                    # One shared payload generation for all clients
                    payload = get_summary_payload()
                    disconnected = []
                    
                    for connection in self.active_connections:
                        try:
                            await connection.send_json(payload)
                        except Exception:
                            disconnected.append(connection)
                            
                    for d in disconnected:
                        self.disconnect(d)
                        
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            pass

broadcaster = TelemetryBroadcaster()

@router.websocket("/stream")
async def stream_analytics(websocket: WebSocket):
    await broadcaster.connect(websocket)
    try:
        while True:
            # Keep connection open, client just listens
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.disconnect(websocket)
