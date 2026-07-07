import sys
import os  # ✅ 添加 os 导入
sys.path.insert(0, '..')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ===== 导入已有的路由 =====
from api_chat import router as chat_router
from api_path import router as path_router
from api_resource import router as resource_router

# ===== 导入知识库路由 =====
from api_knowledge import router as knowledge_router

# ===== 导入 KnowledgeBaseManager =====
knowledge_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'knowledge')
if knowledge_path not in sys.path:
    sys.path.insert(0, knowledge_path)

from KnowledgeBaseManager import KnowledgeBaseManager

app = FastAPI()

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 全局初始化知识库管理器 =====
kb_manager = KnowledgeBaseManager()
print(f"📚 知识库路径: {kb_manager.base_path}")
print(f"📚 已加载知识点数量: {len(kb_manager.topics_index)}")

app.state.kb_manager = kb_manager

# ===== 挂载子路由 =====
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(path_router, prefix="/api/path", tags=["path"])
app.include_router(resource_router, prefix="/api/resource", tags=["resource"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])

# ===== 健康检查 =====
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "knowledge_topics": len(app.state.kb_manager.topics_index),
        "vector_index_ready": app.state.kb_manager._vector_index_ready,
        "embedding_model_loaded": app.state.kb_manager._embedding_model is not None,
    }

@app.get("/")
async def root():
    return {
        "message": "A3 多智能体学习系统",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat",
            "path": "/api/path",
            "resource": "/api/resource",
            "knowledge": "/api/knowledge",
            "health": "/api/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚀 A3 多智能体学习系统启动中...")
    print("📌 API 文档: http://localhost:8080/docs")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8080)