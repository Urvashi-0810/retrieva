from pydantic import BaseModel

class ErrorEvent(BaseModel):
    request_id: str
    error_code: str
    stage: str
    message: str
    recoverable: bool
