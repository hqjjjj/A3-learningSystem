from fastapi import APIRouter
from pydantic import BaseModel
# 注意：这里引入了 get_orchestrator，用来获取总控实例
from orchestrator.orchestrator import handle_chat, get_orchestrator

router = APIRouter()

# ==================== 接口 1：用户发送聊天信息 ====================

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

# ==================== 接口 2：用户登录/刷新页面，拉取完整数据 ====================

class LoadUserRequest(BaseModel):
    user_id: str

@router.post("/user/load")
def load_user(req: LoadUserRequest):
    """
    用户登录或刷新页面时调用。
    返回包含画像、学习路径、推荐资源的完整数据结构。
    """
    orchestrator = get_orchestrator()
    
    # 调用我们在 Orchestrator 里新增的 load_user_state 方法
    # (如果你还没加这个方法，请在 orchestrator.py 里补上我们上一轮写的那个)
    user_state = orchestrator.load_user_state(req.user_id)
    
    return {
        "status": "success",
        "data": user_state
    }