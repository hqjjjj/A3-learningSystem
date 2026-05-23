from fastapi import APIRouter

from orchestrator.orchestrator import get_learning_path

# 用户请求学习路径
router = APIRouter()

@router.get("/{user_id}")
def get_path(user_id: str):

    result = get_learning_path(user_id)

    return {
    "status": "success",
    "data": result
    }

