import os
import json
import glob
from typing import Optional, Dict, List, Any

class KnowledgeBaseManager:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, base_path=None):
        # 防止重复初始化
        if KnowledgeBaseManager._initialized:
            return
            
        if base_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.base_path = current_dir
        else:
            self.base_path = base_path
            
        self.topics_index = {}
        self._load_all_topics()
        
        # ===== 向量检索相关 ===== (这些变量现在不需要了)
        # self._embedding_model = None
        # self.topic_ids = []
        # self.topic_vectors = None
        # self._vector_index_ready = False
        
        # 标记为已初始化
        KnowledgeBaseManager._initialized = True
    
    def _load_all_topics(self):
        """加载 base_path 下所有 JSON 文件中的 topics"""
        json_files = glob.glob(os.path.join(self.base_path, "*.json"))
        print(f"已检索 {len(json_files)} 个 JSON 文件")
        
        for file_path in json_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 处理两种格式：{"topics": [...]} 或 直接是列表
                    if "topics" in data:
                        topics = data["topics"]
                    elif isinstance(data, list):
                        topics = data
                    else:
                        continue
                    for topic in topics:
                        topic_id = topic.get("id")
                        if topic_id:
                            self.topics_index[topic_id] = topic
            except Exception as e:
                print(f"⚠️ 加载文件失败 {file_path}: {e}")
        
        print(f"共加载 {len(self.topics_index)} 个知识点")

    def get_topic_by_id(self, topic_id):
        """根据ID获取知识点"""
        return self.topics_index.get(topic_id)
    
    def get_all_topic_names(self) -> Dict[str, str]:
        """获取所有知识点的名称映射 {id: name}"""
        return {tid: data.get('name', '') for tid, data in self.topics_index.items()}
    
    # ==================== 关键词匹配功能 ====================
    
    def _keyword_match(self, user_input: str) -> Optional[str]:
        """关键词匹配（主要方案）"""
        if not user_input or not user_input.strip():
            return None
        
        user_lower = user_input.lower()
        best_match = None
        best_score = 0
        
        for tid, data in self.topics_index.items():
            name = data.get('name', '').lower()
            if name and name in user_lower:
                score = len(name)
                if score > best_score:
                    best_score = score
                    best_match = tid
            
            content = data.get('content', {})
            if isinstance(content, dict):
                summary = content.get('summary', '').lower()
                if summary and len(summary) > 10:
                    words = user_lower.split()
                    match_count = sum(1 for w in words if w in summary)
                    if match_count > 0:
                        score = match_count * 5
                        if score > best_score:
                            best_score = score
                            best_match = tid
        
        if best_match:
            print(f"🔍 关键词匹配: [{best_match}] {self.topics_index[best_match].get('name', '')}")
            return best_match
        
        return None
    
    def match_topic(self, user_input: str, threshold: float = 0.3, 
               use_semantic: bool = True) -> Optional[str]:
        """智能匹配知识点ID（主入口）"""
        if not user_input or not user_input.strip():
            return None
    
        print(f"\n🔎 正在匹配: \"{user_input}\"")
    
        # 直接使用关键词匹配
        result = self._keyword_match(user_input)
        if result:
            return result
    
        print("❌ 未找到匹配的知识点")
        return None

    
    def match_and_get(self, user_input: str, threshold: float = 0.3) -> Optional[Dict]:
        """匹配并返回知识点数据"""
        topic_id = self.match_topic(user_input, threshold)
        if topic_id:
            return self.get_topic_by_id(topic_id)
        return None
    
    def get_related_topics(self, topic_id: str, max_count: int = 3) -> List[Dict]:
        """获取相关知识点（简化版，返回空列表）"""
        # 由于没有向量索引，无法计算相关性，返回空列表
        return []
    
    def refresh_index(self):
        """刷新索引（简化版，无操作）"""
        # 由于没有向量索引，不需要刷新
        pass
