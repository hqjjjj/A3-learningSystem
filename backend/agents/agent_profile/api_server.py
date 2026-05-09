# api_server.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn

# 导入你的Agent和模型
from profile_agent import ProfileAgent
from models import ProfileResponse

# ==================== 初始化 ====================
app = FastAPI(title="学习画像构建Agent API", version="1.0.0")

# 初始化 Agent (换成你自己的凭证)
import os

agent = ProfileAgent(
    app_id=os.environ.get("SPARK_APP_ID", "820d31b7"),
    api_key=os.environ.get("SPARK_API_KEY", ""),
    api_secret=os.environ.get("SPARK_API_SECRET", "")
)

# ==================== 请求/响应模型 ====================
class BuildProfileRequest(BaseModel):
    """构建画像请求（对齐团队文档）"""
    user_id: str
    user_input: str
    history: Optional[List[Dict[str, str]]] = None
    behavior: Optional[Dict] = None

class ProfileQueryResponse(BaseModel):
    """查询画像响应"""
    profile: dict
    update_type: Optional[str] = None

# ==================== 核心接口 ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """首页：列出所有接口，方便队友调试"""
    return """
    <html>
    <head><title>学习画像构建Agent API</title></head>
    <body>
    <h1>🧠 学习画像构建Agent</h1>
    <p>状态: <span style="color:green">✅ 运行中</span></p>
    <h2>📡 可用接口</h2>
    <ul>
        <li><b>POST /api/profile/build</b> - 构建/更新画像 (主要接口)</li>
        <li><b>GET /api/profile/{user_id}</b> - 查询学生画像</li>
        <li><b>GET /api/profiles</b> - 查看所有学生画像</li>
    </ul>
    </body>
    </html>
    """

@app.post("/api/profile/build", response_model=ProfileResponse)
async def build_profile(request: BuildProfileRequest):
    """
    【核心接口】构建或更新学生画像
    对齐文档输入格式: { user_id, user_input, history, behavior }
    """
    try:
        result = agent.build_profile(
            user_id=request.user_id,
            user_input=request.user_input,
            history=request.history,
            behavior=request.behavior
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    """
    查询特定学生的完整画像
    """
    profile = agent.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="用户画像不存在")
    return {"profile": profile.model_dump(), "update_type": None}

@app.get("/api/profiles")
async def get_all_profiles():
    """
    查看内存中所有学生画像 (调试用)
    """
    all_profiles = agent.get_all_profiles() if hasattr(agent, 'get_all_profiles') else agent.profiles
    return {uid: p.model_dump() for uid, p in all_profiles.items()}

# ==================== 启动 ====================
if __name__ == "__main__":
    print("\n🚀 学习画像Agent API 启动中...")
    print("📍 本地访问: http://127.0.0.1:8000")
    print("📡 队友访问: http://<你的电脑IP>:8000")
    print("📖 API文档: http://127.0.0.1:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)