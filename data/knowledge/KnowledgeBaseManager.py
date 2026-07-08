import os
import json
import glob
import numpy as np
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
        
        # ===== 向量检索相关 =====
        self._embedding_model = None
        self.topic_ids = []
        self.topic_vectors = None
        self._vector_index_ready = False
        
        # 标记为已初始化
        KnowledgeBaseManager._initialized = True
    
    # ... 其余方法保持不变 ...
    
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
    
    # ==================== 向量检索功能 ====================
    
    def _init_embedding_model(self):
        """初始化嵌入模型（懒加载，只在第一次调用时加载）"""
        if self._embedding_model is not None:
            return True
        
        try:
            from sentence_transformers import SentenceTransformer
            print("🔄 正在加载语义匹配模型（首次加载约需10秒）...")
            self._embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            print("✅ 语义匹配模型加载成功")
            return True
        except ImportError:
            print("⚠️ 未安装 sentence-transformers")
            print("   💡 安装命令: pip install sentence-transformers")
            print("   💡 将降级使用关键词匹配")
            self._embedding_model = None
            return False
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            self._embedding_model = None
            return False
    
    def _build_vector_index(self):
        """构建向量索引（将知识点转换为向量）"""
        if not self.topics_index:
            print("⚠️ 知识库为空，无法构建索引")
            return
        
        if self._embedding_model is None:
            return
        
        print(f"🔄 正在构建向量索引（{len(self.topics_index)} 个知识点）...")
        topic_ids = []
        topic_vectors = []
        
        for tid, data in self.topics_index.items():
            # 构建文本表示：名称 + 摘要 + 描述 + 标签
            text_parts = []
            
            if 'name' in data:
                text_parts.append(data['name'])
            
            content = data.get('content', {})
            if isinstance(content, dict):
                if 'summary' in content:
                    text_parts.append(content['summary'])
                if 'description' in content:
                    text_parts.append(content['description'])
            elif isinstance(content, str):
                text_parts.append(content)
            
            if 'tags' in data and isinstance(data['tags'], list):
                text_parts.append(' '.join(data['tags']))
            if 'keywords' in data and isinstance(data['keywords'], list):
                text_parts.append(' '.join(data['keywords']))
            
            text = ' '.join([p for p in text_parts if p])
            if not text.strip():
                text = tid
            
            topic_ids.append(tid)
            topic_vectors.append(self._embedding_model.encode(text))
        
        self.topic_ids = topic_ids
        self.topic_vectors = np.array(topic_vectors)
        self._vector_index_ready = True
        print(f"✅ 向量索引构建完成，向量维度: {self.topic_vectors.shape}")
    
    def _semantic_match(self, user_input: str, threshold: float = 0.3) -> Optional[str]:
        """语义匹配（向量检索）"""
        if not user_input or not user_input.strip():
            return None
        
        if not self._init_embedding_model():
            return None
        
        if not self._vector_index_ready:
            self._build_vector_index()
            if not self._vector_index_ready:
                return None
        
        try:
            query_vec = self._embedding_model.encode(user_input)
            
            norms = np.linalg.norm(self.topic_vectors, axis=1)
            query_norm = np.linalg.norm(query_vec)
            
            if query_norm == 0:
                return None
            
            similarities = np.dot(self.topic_vectors, query_vec) / (norms * query_norm)
            
            best_idx = np.argmax(similarities)
            best_score = similarities[best_idx]
            best_topic_id = self.topic_ids[best_idx]
            best_topic_name = self.topics_index[best_topic_id].get('name', '')
            
            print(f"🔍 语义匹配: [{best_topic_id}] {best_topic_name}, 相似度: {best_score:.3f}")
            
            if best_score < threshold:
                print(f"   ⚠️ 相似度低于阈值 {threshold}，认为不匹配")
                return None
            
            return best_topic_id
            
        except Exception as e:
            print(f"❌ 语义匹配出错: {e}")
            return None
    
    def _keyword_match(self, user_input: str) -> Optional[str]:
        """关键词匹配（备选方案）"""
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
        
        if use_semantic:
            result = self._semantic_match(user_input, threshold)
            if result:
                return result
        
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
        """获取相关知识点"""
        if not self._vector_index_ready:
            return []
        
        try:
            if topic_id not in self.topic_ids:
                return []
            
            idx = self.topic_ids.index(topic_id)
            target_vector = self.topic_vectors[idx]
            
            norms = np.linalg.norm(self.topic_vectors, axis=1)
            similarities = np.dot(self.topic_vectors, target_vector) / (norms * norms[idx])
            
            similarities[idx] = -1
            top_indices = np.argsort(similarities)[::-1][:max_count]
            
            related = []
            for i in top_indices:
                if similarities[i] > 0.2:
                    tid = self.topic_ids[i]
                    related.append({
                        'topic_id': tid,
                        'name': self.topics_index[tid].get('name', ''),
                        'similarity': float(similarities[i])
                    })
            
            return related
        except Exception as e:
            print(f"⚠️ 获取相关知识点失败: {e}")
            return []
    
    def refresh_index(self):
        """刷新向量索引"""
        self._vector_index_ready = False
        self.topic_ids = []
        self.topic_vectors = None
        self._build_vector_index()