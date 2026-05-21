import uvicorn
import sys
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents', 'agent_profile'))
from profile_agent import ProfileAgent

app = FastAPI(title="A3 学习画像Agent", version="1.0.0")

profile_agent = ProfileAgent(
    app_id="820d31b7",
    api_key="6e31903de32ff6578f5d5e5e137d5328",
    api_secret="MDgyODNjMTg1MzdjZGM5YTU4NDlmYWNh"
)

class BuildProfileRequest(BaseModel):
    user_id: str
    user_input: str
    history: Optional[List[Dict]] = None
    behavior: Optional[Dict] = None

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <h1>✅ A3 多智能体学习系统</h1>
    <ul>
        <li>POST /api/profile/build</li>
        <li>GET /api/profile/{user_id}</li>
        <li>GET /api/profiles</li>
    </ul>
    """

@app.post("/api/profile/build")
async def build_profile(request: BuildProfileRequest):
    return profile_agent.build_profile(
        user_id=request.user_id,
        user_input=request.user_input,
        history=request.history,
        behavior=request.behavior
    )

@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    profile = profile_agent.get_profile(user_id)
    if not profile:
        return {"error": "用户不存在"}
    return {"profile": profile.model_dump()}

@app.get("/api/profiles")
async def get_all_profiles():
    return {uid: p.model_dump() for uid, p in profile_agent.profiles.items()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)