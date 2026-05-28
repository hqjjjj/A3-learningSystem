from fastapi import APIRouter
from pydantic import BaseModel

from orchestrator.orchestrator import get_learning_path

# 用户请求学习路径
router = APIRouter()

class PathRequest(BaseModel):
    user_id: str
    topic: str 

@router.post("/") 
def get_path(req: PathRequest):
    result = get_learning_path(
        user_id=req.user_id,
        topic=req.topic
    )
    return {
        "status": "success",
        "data": result
    }
