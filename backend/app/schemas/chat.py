from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatMessage(BaseModel):
    role: str # user, assistant, system, tool
    content: str

class ChatRequest(BaseModel):
    message: str
    camera_id: Optional[str] = None
    conversation_history: Optional[List[ChatMessage]] = []

class ToolCallInfo(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Any

class ChatResponse(BaseModel):
    answer: str
    tool_calls: List[ToolCallInfo] = []
    referenced_events: List[Dict[str, Any]] = []
    referenced_clips: List[str] = []
