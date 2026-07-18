"""
知识库相关 API 路由
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, Dict, List
import json
import os

router = APIRouter()

#  请求/响应模型 



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
    related_topics: Optional[List[Dict]] = None
    matched_by: str = "none"

class KnowledgeChatRequest(BaseModel):
    """知识库对话请求"""
    user_id: str
    message: str
    history: Optional[List[Dict]] = None
    threshold: float = 0.3

class KnowledgeChatResponse(BaseModel):
    """知识库对话响应"""
    user_id: str
    message: str
    topic_id: Optional[str] = None
    topic_name: Optional[str] = None
    topic_content: Optional[Dict] = None
    related_topics: Optional[List[Dict]] = None

#  辅助函数：获取 kb_manager 

def get_kb_manager(request: Request):
    """从 app.state 获取知识库管理器"""
    return request.app.state.kb_manager

#  API 路由 

@router.get("/chapters")
async def get_chapters():
    """
    获取知识图谱所有章节列表
    从 data/knowledge/index.json 读取
    """
    try:
        # 获取 knowledge 目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        knowledge_dir = os.path.join(current_dir, '..', '..', 'data', 'knowledge')
        index_path = os.path.join(knowledge_dir, 'index.json')
        
        with open(index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    except FileNotFoundError:
        return {
            "error": "index.json not found",
            "course": "操作系统",
            "totalChapters": 0,
            "chapters": []
        }
    except Exception as e:
        return {
            "error": str(e),
            "course": "操作系统",
            "totalChapters": 0,
            "chapters": []
        }


@router.get("/chapter/{filename}")
async def get_chapter(filename: str):
    """
    获取单个章节内容
    从 data/knowledge/{filename} 读取
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        knowledge_dir = os.path.join(current_dir, '..', '..', 'data', 'knowledge')
        file_path = os.path.join(knowledge_dir, filename)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    except FileNotFoundError:
        return {"error": f"文件 {filename} 不存在", "topics": []}
    except Exception as e:
        return {"error": str(e), "topics": []}

@router.post("/match", response_model=KnowledgeMatchResponse)
async def match_knowledge(request: Request, req: KnowledgeMatchRequest):
    """
    语义匹配知识点
    """
    kb_manager = get_kb_manager(request)
    
    topic_id = kb_manager.match_topic(req.query, threshold=req.threshold)
    
    response = KnowledgeMatchResponse(
        query=req.query,
        topic_id=topic_id
    )
    
    if topic_id:
        topic_data = kb_manager.get_topic_by_id(topic_id)
        response.topic_name = topic_data.get('name', '')
        response.topic_content = topic_data if req.return_content else None
        response.matched_by = "semantic"
        
        if req.return_content:
            related = kb_manager.get_related_topics(topic_id, max_count=3)
            response.related_topics = related
    else:
        response.matched_by = "none"
    
    return response


@router.post("/chat", response_model=KnowledgeChatResponse)
async def chat_with_knowledge(request: Request, req: KnowledgeChatRequest):
    """
    带知识库的对话接口
    1. 匹配知识点
    2. 返回知识点内容
    """
    kb_manager = get_kb_manager(request)
    
    topic_id = kb_manager.match_topic(req.message, threshold=req.threshold)
    
    response = KnowledgeChatResponse(
        user_id=req.user_id,
        message=req.message,
        topic_id=topic_id
    )
    
    if topic_id:
        topic_data = kb_manager.get_topic_by_id(topic_id)
        response.topic_name = topic_data.get('name', '')
        response.topic_content = topic_data
        
        related = kb_manager.get_related_topics(topic_id, max_count=3)
        response.related_topics = related
    
    return response


@router.get("/topics")
async def get_all_topics(request: Request):
    """
    获取所有知识点列表（精简版）
    """
    kb_manager = get_kb_manager(request)
    
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


@router.get("/topic/{topic_id}")
async def get_topic(request: Request, topic_id: str, include_related: bool = False):
    """
    获取特定知识点详情
    """
    kb_manager = get_kb_manager(request)
    
    topic_data = kb_manager.get_topic_by_id(topic_id)
    if not topic_data:
        return {"error": f"知识点 {topic_id} 不存在"}
    
    result = {"topic": topic_data}
    
    if include_related:
        related = kb_manager.get_related_topics(topic_id, max_count=5)
        result["related_topics"] = related
    
    return result


@router.post("/refresh")
async def refresh_knowledge(request: Request):
    """
    刷新知识库索引（当知识库文件更新时调用）
    """
    kb_manager = get_kb_manager(request)
    
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


@router.get("/search")
async def search_knowledge(request: Request, q: str, threshold: float = 0.3):
    """
    搜索知识点（简化版）
    """
    kb_manager = get_kb_manager(request)
    
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


@router.get("/stats")
async def get_knowledge_stats(request: Request):
    """
    获取知识库统计信息
    """
    kb_manager = get_kb_manager(request)
    
    return {
        "total_topics": len(kb_manager.topics_index),
        "vector_index_ready": kb_manager._vector_index_ready,
        "embedding_model_loaded": kb_manager._embedding_model is not None,
        "base_path": kb_manager.base_path
    }