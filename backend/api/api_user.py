# 作用：主动从后端加载用户已有的持久化数据
# backend/api/api_user.py
from fastapi import APIRouter
from pydantic import BaseModel
from orchestrator.orchestrator import load_user_state

router = APIRouter()

class UserStateRequest(BaseModel):
    user_id: str

@router.post("/load_state")
def load_state(req: UserStateRequest):
    result = load_user_state(req.user_id)
    return {
        "status": "success",
        "data": result
    }