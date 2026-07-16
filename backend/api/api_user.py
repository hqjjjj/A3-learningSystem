# 作用：主动从后端加载用户已有的持久化数据
# backend/api/api_user.py
from fastapi import APIRouter
from pydantic import BaseModel
from orchestrator.orchestrator import get_orchestrator
router = APIRouter()

class UserStateRequest(BaseModel):
    user_id: str

# backend/api/api_user.py
@router.post("/load_state")
def load_state(req: UserStateRequest):
    orchestrator = get_orchestrator()
    result = orchestrator.load_user_state(req.user_id)
    return {
        "status": "success",
        "data": result
    }
