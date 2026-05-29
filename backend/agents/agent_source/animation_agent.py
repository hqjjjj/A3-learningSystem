# backend/agents/agent_source/animation_agent.py
from backend.agents.agent_source.animation_prompt import system_prompt_animation
from backend.agents.agent_source.user_prompt import user_prompt_animation_build
from data.knowledge.KnowledgeBaseManager import KnowledgeBaseManager
from backend.agents.agent_source.lmm import SparkLLM
import json
import os
from json_repair import repair_json
import time
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "cache"
CACHE_FILE = CACHE_DIR / "animation_cache.json"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
kb = KnowledgeBaseManager(os.path.join(BASE_DIR, "data/knowledge"))
llm = SparkLLM()

def parse_output(result):
    fixed = repair_json(result)
    try:
        return json.loads(fixed)
    except Exception as e:
        return {"error": str(e), "raw": result}

# 动画缓存机制
import json
import os
import hashlib
from pathlib import Path

# 缓存文件路径（放在项目 data 目录下）
CACHE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "cache"
CACHE_FILE = CACHE_DIR / "animation_cache.json"

class AnimationCache:
    """动画缓存管理器"""
    def __init__(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.cache = self._load()
    
    def _load(self):
        """从文件加载缓存"""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save(self):
        """保存缓存到文件"""
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def _make_key(self, topic_id, resource_type):
        """生成缓存键"""
        raw = f"{topic_id}:{resource_type}"
        return hashlib.md5(raw.encode()).hexdigest()
    
    def get(self, topic_id, resource_type):
        """获取缓存，返回 (html_content, title, description) 或 None"""
        key = self._make_key(topic_id, resource_type)
        entry = self.cache.get(key)
        if entry:
            return entry.get("html_content"), entry.get("title"), entry.get("description")
        return None
    
    def set(self, topic_id, resource_type, html_content, title, description):
        """存入缓存"""
        key = self._make_key(topic_id, resource_type)
        self.cache[key] = {
            "html_content": html_content,
            "title": title,
            "description": description,
            "created_at": __import__("time").time()
        }
        self._save()

# 全局单例
_cache = AnimationCache()



class agentanimation:
    def run(self, input_data, topic):
        topic_id = input_data["topic_id"]
        resource_type = "animation"
        
        if topic is None:
            return {"error": f"知识点不存在: {topic_id}"}
        
        # 检查缓存
        cached = _cache.get(topic_id, resource_type)
        if cached:
            html_content, title, description = cached
            print(f"动画缓存命中: {topic_id}")
            return {"animation": {
                "type": "html",
                "title": title,
                "html_content": html_content,
                "description": description
            }}
        
        system = system_prompt_animation
        user = user_prompt_animation_build(input_data, topic, kb)
        
        for i in range(1):
            t0 = time.time()
            result = llm.generate(system, user)
            print(f"LLM 调用耗时（第{i+1}次）: {time.time()-t0:.2f}秒")
            
            parsed = parse_output(result)
            # 确保 parsed 是字典
            if not isinstance(parsed, dict):
                if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict):
                    parsed = parsed[0]
                else:
                    parsed = {"error": "返回结果不是JSON对象", "raw": result}
            
            if "error" not in parsed and "animation" in parsed:
                anim_data = parsed["animation"]
                anim = {}
                if isinstance(anim_data, dict):
                    anim = anim_data
                elif isinstance(anim_data, list):
                    for item in anim_data:
                        if isinstance(item, dict):
                            anim = item
                            break
                if not isinstance(anim, dict):
                    anim = {}
                
                anim.setdefault("type", "html")
                anim.setdefault("title", f"{input_data.get('module', '动画')}演示")
                anim.setdefault("html_content", "")
                anim.setdefault("description", "")
                
                if not anim["html_content"].strip():
                    anim["html_content"] = "<div style='padding:20px;text-align:center;color:red;'>动画生成失败，请重试</div>"
                
                _cache.set(topic_id, resource_type, 
                          anim["html_content"], anim["title"], anim.get("description", ""))
                
                return {"animation": anim}
            else:
                user += f"\n你上次输出的JSON不合法，错误：{parsed.get('error')}，请重新输出合法JSON。"
        
        return {"error": "动画生成重试失败"}