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




class agentanimation:
    def run(self, input_data, topic):
        topic_id = input_data["topic_id"]
        resource_type = "animation"
        
        if topic is None:
            return {"error": f"知识点不存在: {topic_id}"}
        
        
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
                
                
                return {"animation": anim}
            else:
                user += f"\n你上次输出的JSON不合法，错误：{parsed.get('error')}，请重新输出合法JSON。"
        
        return {"error": "动画生成重试失败"}