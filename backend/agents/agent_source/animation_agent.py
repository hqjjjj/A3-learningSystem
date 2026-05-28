# backend/agents/agent_source/animation_agent.py
from backend.agents.agent_source.animation_prompt import system_prompt_animation
from backend.agents.agent_source.user_prompt import user_prompt_build
from data.knowledge.KnowledgeBaseManager import KnowledgeBaseManager
from backend.agents.agent_source.lmm import SparkLLM
import json
import os
from json_repair import repair_json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
kb = KnowledgeBaseManager(os.path.join(BASE_DIR, "data/knowledge"))
llm = SparkLLM()

def parse_output(result):
    fixed = repair_json(result)
    try:
        return json.loads(fixed)
    except Exception as e:
        return {"error": str(e), "raw": result}

class agentanimation:
    def run(self, input_data, topic):
        system = system_prompt_animation
        user = user_prompt_build(input_data, topic, kb)
        for i in range(3):
            result = llm.generate(system, user)
            parsed = parse_output(result)
            if "error" not in parsed and "animation" in parsed:
                anim = parsed["animation"]
                # 补全字段
                anim.setdefault("type", "html")
                anim.setdefault("title", f"{input_data.get('module', '动画')}演示")
                anim.setdefault("html_content", "")
                anim.setdefault("description", "")
                # 强制确保 html_content 非空
                if not anim["html_content"].strip():
                    anim["html_content"] = "<div style='padding:20px;text-align:center;color:red;'>动画生成失败，请重试</div>"
                # 添加 subtype 标识
                return {"animation": anim}
            else:
                user += f"\n你上次输出的JSON不合法，错误：{parsed.get('error')}，请重新输出合法JSON。"
        return {"error": "动画生成重试失败"}