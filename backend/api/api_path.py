#D:\软件杯\UserModelingAgent\backend\api\api_path.py
from fastapi import APIRouter
from pydantic import BaseModel
from backend.orchestrator.orchestrator import get_orchestrator

router = APIRouter()

class PathRequest(BaseModel):
    user_id: str
    topic: str 

@router.post("/") 
def get_path(req: PathRequest):
    orchestrator = get_orchestrator()
    
    # 先更新主题并获取路径（内部会调用 _call_plan_agent，结果会被缓存）
    orchestrator.get_learning_path(req.user_id, req.topic)
    
    #加载完整状态（包括资源和路径，会命中路径缓存，并生成资源）
    full_state = orchestrator.load_user_state(req.user_id)
    
    # 直接返回数据（与 load_user_state 保持一致，不额外包装）
    return {
        "learning_path": full_state.get("learning_path"),  # 对象 {current, next, path_list}
        "recommended_resources": full_state.get("recommended_resources", [])
    }