from typing import Dict, List
from app.schemas.pipeline import PipelineState, VALID_TRANSITIONS

class PipelineStateMachine:
    def __init__(self, initial_state: PipelineState = PipelineState.REQUEST_RECEIVED):
        self.current_state = initial_state

    def transition(self, next_state: PipelineState) -> bool:
        """Transitions to the next state if valid."""
        if next_state in VALID_TRANSITIONS.get(self.current_state, []):
            self.current_state = next_state
            return True
        # Always allow transition to ERROR or CANCELLED from any state for safety
        if next_state in [PipelineState.ERROR, PipelineState.CANCELLED]:
             self.current_state = next_state
             return True
             
        raise ValueError(f"Invalid transition from {self.current_state.name} to {next_state.name}")
        
    def get_state(self) -> PipelineState:
        return self.current_state
