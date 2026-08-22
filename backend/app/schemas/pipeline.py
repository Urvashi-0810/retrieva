from enum import Enum
from pydantic import BaseModel
from typing import Dict, List

class PipelineState(str, Enum):
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    TRANSCRIBING = "TRANSCRIBING"
    QUERY_READY = "QUERY_READY"
    CACHE_CHECK = "CACHE_CHECK"
    CACHE_HIT = "CACHE_HIT"
    CACHE_MISS = "CACHE_MISS"
    RETRIEVING = "RETRIEVING"
    RETRIEVAL_VALIDATED = "RETRIEVAL_VALIDATED"
    GENERATING = "GENERATING"
    STREAMING = "STREAMING"
    GROUNDED = "GROUNDED"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"

# Define valid transitions for state machine
VALID_TRANSITIONS: Dict[PipelineState, List[PipelineState]] = {
    PipelineState.REQUEST_RECEIVED: [PipelineState.TRANSCRIBING, PipelineState.QUERY_READY, PipelineState.ERROR, PipelineState.CANCELLED],
    PipelineState.TRANSCRIBING: [PipelineState.QUERY_READY, PipelineState.ERROR, PipelineState.CANCELLED],
    PipelineState.QUERY_READY: [PipelineState.CACHE_CHECK, PipelineState.ERROR, PipelineState.CANCELLED],
    PipelineState.CACHE_CHECK: [PipelineState.CACHE_HIT, PipelineState.CACHE_MISS, PipelineState.ERROR, PipelineState.CANCELLED],
    PipelineState.CACHE_HIT: [PipelineState.STREAMING, PipelineState.ERROR, PipelineState.CANCELLED],
    PipelineState.CACHE_MISS: [PipelineState.RETRIEVING, PipelineState.ERROR, PipelineState.CANCELLED],
    PipelineState.RETRIEVING: [PipelineState.RETRIEVAL_VALIDATED, PipelineState.ERROR, PipelineState.CANCELLED],
    PipelineState.RETRIEVAL_VALIDATED: [PipelineState.GENERATING, PipelineState.ERROR, PipelineState.CANCELLED],
    PipelineState.GENERATING: [PipelineState.STREAMING, PipelineState.ERROR, PipelineState.CANCELLED],
    PipelineState.STREAMING: [PipelineState.GROUNDED, PipelineState.ERROR, PipelineState.CANCELLED],
    PipelineState.GROUNDED: [PipelineState.COMPLETED, PipelineState.ERROR, PipelineState.CANCELLED],
    PipelineState.COMPLETED: [],
    PipelineState.ERROR: [],
    PipelineState.CANCELLED: [],
}
