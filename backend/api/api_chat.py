from fastapi import APIRouter
from pydantic import BaseModel
from backend.orchestrator.orchestrator import handle_chat

router = APIRouter()

# 用户发送聊天信息

class ChatRequest(BaseModel):
    user_id: str
    message: str
    topic: str = None

@router.post("/")
def chat(req: ChatRequest):
    result = handle_chat(user_id=req.user_id, message=req.message, topic=req.topic)
    return {
        "status": "success",
        "data": result
    }

