import uvicorn
import sys
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, List

# 添加 agents 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents', 'agent_profile'))
from profile_agent import ProfileAgent

# ===== 导入 KnowledgeBaseManager（调整路径） =====
# 获取项目根目录（backend 的父目录）
project_root = os.path.dirname(os.path.dirname(__file__))
# 添加 data/knowledge 到 sys.path
knowledge_path = os.path.join(project_root, 'data', 'knowledge')
sys.path.insert(0, knowledge_path)

# 现在可以导入 KnowledgeBaseManager
from KnowledgeBaseManager import KnowledgeBaseManager

app = FastAPI(title="A3 多智能体学习系统", version="1.0.0")

# ========== 初始化所有组件 ==========

# 1. 初始化画像 Agent
profile_agent = ProfileAgent(
    app_id="820d31b7",
    api_key="6e31903de32ff6578f5d5e5e137d5328",
    api_secret="MDgyODNjMTg1MzdjZGM5YTU4NDlmYWNh"
)

# 2. 初始化知识库管理器
# 注意：KnowledgeBaseManager 在 data/knowledge 下，需要传入正确的路径
knowledge_base_path = knowledge_path  # 就是 data/knowledge
kb_manager = KnowledgeBaseManager(knowledge_base_path)
print(f"📚 知识库路径: {knowledge_base_path}")
print(f"📚 已加载知识点数量: {len(kb_manager.topics_index)}")

# ========== 请求/响应模型 ==========

class BuildProfileRequest(BaseModel):
    user_id: str
    user_input: str
    history: Optional[List[Dict]] = None
    behavior: Optional[Dict] = None

class ChatRequest(BaseModel):
    """对话请求"""
    user_id: str
    message: str
    history: Optional[List[Dict]] = None
    threshold: float = 0.3  # 语义匹配阈值

class ChatResponse(BaseModel):
    """对话响应"""
    user_id: str
    message: str
    topic_id: Optional[str] = None
    topic_name: Optional[str] = None
    topic_content: Optional[Dict] = None
    related_topics: Optional[List[Dict]] = None
    profile_updated: bool = False

class KnowledgeMatchRequest(BaseModel):
    """纯知识点匹配请求"""
    query: str
    threshold: float = 0.3
    return_content: bool = False

class KnowledgeMatchResponse(BaseModel):
    """知识点匹配响应"""
    query: str
    topic_id: Optional[str] = None
    topic_name: Optional[str] = None
    topic_content: Optional[Dict] = None
    similarity_score: Optional[float] = None
    related_topics: Optional[List[Dict]] = None
    matched_by: str = "none"  # semantic, keyword, none

# ========== 原有 API 保持不变 ==========

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <h1>✅ A3 多智能体学习系统</h1>
    <ul>
        <li><strong>画像系统</strong></li>
        <li>POST /api/profile/build - 构建用户画像</li>
        <li>GET /api/profile/{user_id} - 获取用户画像</li>
        <li>GET /api/profiles - 获取所有画像</li>
        <li><strong>知识库系统（新增）</strong></li>
        <li>POST /api/knowledge/match - 语义匹配知识点</li>
        <li>POST /api/knowledge/chat - 带知识库的对话</li>
        <li>GET /api/knowledge/topics - 获取所有知识点列表</li>
        <li>GET /api/knowledge/topic/{topic_id} - 获取特定知识点</li>
        <li>POST /api/knowledge/refresh - 刷新知识库索引</li>
        <li><strong>工具</strong></li>
        <li>GET /api/health - 健康检查</li>
    </ul>
    """

# ========== 原有画像 API ==========

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

# ========== 新增：知识库 API ==========

@app.post("/api/knowledge/match", response_model=KnowledgeMatchResponse)
async def match_knowledge(request: KnowledgeMatchRequest):
    """
    语义匹配知识点
    """
    # 执行匹配
    topic_id = kb_manager.match_topic(request.query, threshold=request.threshold)
    
    response = KnowledgeMatchResponse(
        query=request.query,
        topic_id=topic_id
    )
    
    if topic_id:
        topic_data = kb_manager.get_topic_by_id(topic_id)
        response.topic_name = topic_data.get('name', '')
        response.topic_content = topic_data if request.return_content else None
        response.matched_by = "semantic"
        
        # 获取相关知识点
        if request.return_content:
            related = kb_manager.get_related_topics(topic_id, max_count=3)
            response.related_topics = related
    else:
        response.matched_by = "none"
    
    return response

@app.post("/api/knowledge/chat")
async def chat_with_knowledge(request: ChatRequest):
    """
    带知识库的对话接口
    1. 匹配知识点
    2. 更新用户画像（如果有）
    3. 返回知识点内容
    """
    # 1. 匹配知识点
    topic_id = kb_manager.match_topic(request.message, threshold=request.threshold)
    
    response = ChatResponse(
        user_id=request.user_id,
        message=request.message,
        topic_id=topic_id
    )
    
    # 2. 如果匹配到知识点，获取内容
    if topic_id:
        topic_data = kb_manager.get_topic_by_id(topic_id)
        response.topic_name = topic_data.get('name', '')
        response.topic_content = topic_data
        
        # 3. 获取相关知识点（用于上下文扩展）
        related = kb_manager.get_related_topics(topic_id, max_count=3)
        response.related_topics = related
        
        # 4. 更新用户画像（记录学习行为）
        try:
            behavior = {
                "action": "knowledge_query",
                "topic_id": topic_id,
                "topic_name": response.topic_name,
                "timestamp": "now"
            }
            
            profile_agent.build_profile(
                user_id=request.user_id,
                user_input=f"学习了知识点: {response.topic_name}",
                history=request.history,
                behavior=behavior
            )
            response.profile_updated = True
        except Exception as e:
            print(f"⚠️ 更新画像失败: {e}")
    
    return response

@app.get("/api/knowledge/topics")
async def get_all_topics():
    """
    获取所有知识点列表（精简版）
    """
    topics = []
    for tid, data in kb_manager.topics_index.items():
        summary = ""
        content = data.get('content', {})
        if isinstance(content, dict):
            summary = content.get('summary', '')[:100]
        elif isinstance(content, str):
            summary = content[:100]
            
        topics.append({
            "id": tid,
            "name": data.get('name', ''),
            "summary": summary
        })
    return {
        "total": len(topics),
        "topics": topics
    }

@app.get("/api/knowledge/topic/{topic_id}")
async def get_topic(topic_id: str, include_related: bool = False):
    """
    获取特定知识点详情
    """
    topic_data = kb_manager.get_topic_by_id(topic_id)
    if not topic_data:
        return {"error": f"知识点 {topic_id} 不存在"}
    
    result = {"topic": topic_data}
    
    if include_related:
        related = kb_manager.get_related_topics(topic_id, max_count=5)
        result["related_topics"] = related
    
    return result

@app.post("/api/knowledge/refresh")
async def refresh_knowledge():
    """
    刷新知识库索引（当知识库文件更新时调用）
    """
    try:
        kb_manager._load_all_topics()
        kb_manager.refresh_index()
        return {
            "status": "success",
            "message": "知识库已刷新",
            "total_topics": len(kb_manager.topics_index)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"刷新失败: {e}"
        }

@app.get("/api/knowledge/search")
async def search_knowledge(q: str, threshold: float = 0.3):
    """
    搜索知识点（简化版）
    """
    topic_id = kb_manager.match_topic(q, threshold=threshold)
    if not topic_id:
        return {
            "query": q,
            "found": False,
            "message": "未找到匹配的知识点"
        }
    
    topic_data = kb_manager.get_topic_by_id(topic_id)
    summary = ""
    content = topic_data.get('content', {})
    if isinstance(content, dict):
        summary = content.get('summary', '')
    elif isinstance(content, str):
        summary = content
    
    return {
        "query": q,
        "found": True,
        "topic_id": topic_id,
        "topic_name": topic_data.get('name', ''),
        "summary": summary,
        "related": kb_manager.get_related_topics(topic_id, max_count=3)
    }

# ========== 健康检查 ==========

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "knowledge_topics": len(kb_manager.topics_index),
        "vector_index_ready": kb_manager._vector_index_ready,
        "embedding_model_loaded": kb_manager._embedding_model is not None,
        "profiles": len(profile_agent.profiles)
    }

# ========== 启动入口 ==========

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 A3 多智能体学习系统启动中...")
    print(f"📚 知识库路径: {knowledge_base_path}")
    print(f"📚 知识点数量: {len(kb_manager.topics_index)}")
    print(f"👤 画像系统: 已初始化")
    print("=" * 50)
    print("📌 API 文档: http://localhost:8080/docs")
    print("📌 知识库匹配: POST /api/knowledge/match")
    print("📌 智能对话: POST /api/knowledge/chat")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8080)