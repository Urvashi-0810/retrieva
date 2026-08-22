import collections
import threading
from typing import List, Dict
from app.telemetry.metrics import calculate_critical_paths
from app.telemetry.percentiles import calculate_percentiles

class TelemetryCollector:
    def __init__(self, max_capacity: int = 1000):
        self.max_capacity = max_capacity
        self.buffer = collections.deque(maxlen=self.max_capacity)
        self.lock = threading.Lock()

    def add_record(self, record: dict) -> None:
        enriched_record = calculate_critical_paths(record)
        with self.lock:
            self.buffer.append(enriched_record)

    def get_snapshot(self) -> List[Dict]:
        with self.lock:
            return list(self.buffer)

    def get_percentiles(self) -> dict:
        snapshot = self.get_snapshot()
        rag_samples = []
        audio_samples = []
        
        for record in snapshot:
            rag = record.get("rag_hot_path_ms")
            audio = record.get("audio_to_first_response_ms")
            if rag is not None:
                rag_samples.append(rag)
            if audio is not None:
                audio_samples.append(audio)
                
        return {
            "rag_hot_path": calculate_percentiles(rag_samples),
            "audio_to_first_response": calculate_percentiles(audio_samples)
        }
