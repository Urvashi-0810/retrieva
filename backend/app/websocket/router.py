import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from datetime import datetime
import json

from app.services.vad import SileroVADService
from app.services.stt import SarvamSTTService
from app.schemas.events import TranscriptEvent, WebSocketEvent
from app.dependencies import get_orchestrator
from app.pipeline.orchestrator import PipelineOrchestrator

router = APIRouter()

# Initialize your services
vad_service = SileroVADService()
stt_service = SarvamSTTService()

@router.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket, orchestrator: PipelineOrchestrator = Depends(get_orchestrator)):
    await websocket.accept()
    
    # We will store the audio frames here while the user is actively speaking
    audio_buffer = bytearray()
    is_speaking = False
    
    try:
        while True:
            # 1. Receive data from the frontend
            data = await websocket.receive_text()
            client_event = json.loads(data)
            
            if client_event["type"] == "audio_chunk":
                import base64
                request_id = client_event["request_id"]
                raw_audio_bytes = base64.b64decode(client_event["data"]["audio_data"])
                
                # 2. Feed the audio into your VAD
                speech_detected = await vad_service.process_audio_frame(raw_audio_bytes)
                
                if speech_detected:
                    # User is currently talking, save the audio!
                    is_speaking = True
                    audio_buffer.extend(raw_audio_bytes)
                    
                elif is_speaking and not speech_detected:
                    # User was speaking, but just stopped (Silence detected)
                    is_speaking = False
                    
                    if len(audio_buffer) > 0:
                        print("Speech ended, sending to STT...")
                        
                        # 3. Send the full buffered sentence to Sarvam
                        transcribed_text = await stt_service.transcribe(bytes(audio_buffer))
                        
                        # Clear the buffer for the next sentence
                        audio_buffer.clear()
                        
                        if transcribed_text:
                            # 4. Create the exact Contract Person 1 asked for
                            transcript_event = TranscriptEvent(
                                request_id=request_id,
                                text=transcribed_text,
                                is_final=True,
                                stability=1.0
                            )
                            
                            # 5. Send it back out
                            response = WebSocketEvent(
                                type="transcript_final",
                                request_id=request_id,
                                timestamp=datetime.utcnow(),
                                data=transcript_event.dict()
                            )
                            await websocket.send_text(response.json())
                            
                            # 6. Feed to orchestrator and stream LLM response
                            async for token in orchestrator.process_query(request_id, transcribed_text):
                                llm_event = WebSocketEvent(
                                    type="llm_token",
                                    request_id=request_id,
                                    timestamp=datetime.utcnow(),
                                    data={"token": token}
                                )
                                await websocket.send_text(llm_event.json())

    except WebSocketDisconnect:
        print("Client disconnected normally.")
    except Exception as e:
        print(f"WebSocket Error: {e}")
        # Send a typed error event if something crashes
        error_event = WebSocketEvent(
            type="error",
            request_id="unknown",
            data={"error_code": "WS_ERROR", "message": str(e), "stage": "voice_ingestion"}
        )
        await websocket.send_text(error_event.json())