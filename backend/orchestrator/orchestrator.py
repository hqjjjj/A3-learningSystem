# backend/orchestrator/orchestrator.py
import sys
import os
import json
from typing import Dict, Optional, List
from datetime import datetime

# 导入画像Agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents', 'agent_profile'))
from profile_agent import ProfileAgent

# 导入队友A 路径规划
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents', 'agent_plan'))
from agentplan import run_planner

# 导入队友C 资源生成
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents', 'agent_source'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.agents.agent_source.kn_agent import agentkn as kn_agent_class
from backend.agents.agent_source.code_agent import agentcode as code_agent_class
from backend.agents.agent_source.exercise_agent import agentexercise as exercise_agent_class
from backend.agents.agent_source.main import generate_resources


class Orchestrator:
    """多智能体总控调度器"""

    def __init__(self):
        self.profile_agent = ProfileAgent()
        self.behavior_log = []
        self.kn_agent = kn_agent_class()
        self.code_agent = code_agent_class()
        self.exercise_agent = exercise_agent_class()
        self.memory_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'data', 'knowledge', 'memory.json'
        )

    # ==================== 五个核心函数 ====================

    def handle_chat(self, user_id: str, message: str, topic: str = None) -> Dict:
        self._log_behavior(user_id, "chat", message)
        
        # 1. 关键修复：强制更新画像
        profile_dict = self._update_profile(user_id, message)
        
        # 2. 如果前端明确指定了 Topic，强制更新画像对象的 current_topic
        if topic:
            profile_obj = self.profile_agent.get_profile(user_id)
            if profile_obj:
                profile_obj.progress.current_topic = topic
                # 保存到磁盘（保证跨服务重启依旧有效）
                self.profile_agent._save_profile_to_disk(profile_obj)
                profile_dict = profile_obj.model_dump()
        
        # 3. 规划路径（传字典即可）
        path_data = self._call_plan_agent(user_id, profile_dict)
        
        # 4. 生成资源
        resources = self._call_source_agent(profile_dict, path_data)
        
        # 5. 生成回复
        reply = self._generate_reply(profile_dict, path_data)
        recommended = self._extract_recommended(resources)

        return {
            "reply": reply,
            "profile": profile_dict, # 返回最新的完整画像
            "learning_path": path_data.get("path_list", []),
            "recommended_resources": recommended,
            "topic": profile_dict.get("progress", {}).get("current_topic", ""),
            "current_progress": path_data.get("current_progress", "")
        }

    def get_learning_path(self, user_id: str, topic: str = None) -> Dict:
        profile_obj = self.profile_agent.get_profile(user_id)
        
        # 如果内存里没有，尝试从磁盘加载
        if not profile_obj:
            profile_obj = self.profile_agent.load_profile_from_disk(user_id)
            if profile_obj:
                self.profile_agent.profiles[user_id] = profile_obj

        profile_dict = profile_obj.model_dump() if profile_obj else {}
        
        path_data = self._call_plan_agent(user_id, profile_dict)
        return {
            "profile": profile_dict,
            "learning_path": path_data.get("path_list", []),
            "topic": profile_dict.get("progress", {}).get("current_topic", ""),
            "current_progress": path_data.get("current_progress", "")
        }

    def generate_single_resource(self, user_id: str, topic: str, resource_type: str) -> Dict:
        profile = self._get_profile_dict(user_id)
        resource_input = self._build_resource_input(profile, None)
        resource_input["topic_id"] = topic
        resource_input["resource_type"] = [resource_type]
        resources = self._call_source_agent_raw(resource_input)
        return {
            "generated_resource": resources[0] if resources else {},
            "topic": topic,
            "current_progress": profile.get("progress", {}).get("current_topic", "")
        }

    def finish_view_resource(self, user_id: str, resource_id: str, duration: int) -> Dict:
        self._log_behavior(user_id, "view_resource", f"resource:{resource_id}", duration)
        profile = self._update_profile(user_id, f"学习了资源{resource_id}，用时{duration}秒")
        path_data = self._call_plan_agent(user_id, profile)
        resources = self._call_source_agent(profile, path_data)
        recommended = self._extract_recommended(resources)

        return {
            "profile": profile,
            "learning_path": path_data.get("path_list", []),
            "recommended_resources": recommended,
            "topic": profile.get("progress", {}).get("current_topic", ""),
            "current_progress": path_data.get("current_progress", "")
        }

    def submit_answer_result(self, user_id: str, topic: str, correct_rate: float, duration: int) -> Dict:
        self._log_behavior(user_id, "submit_answer", topic, duration, correct_rate)
        profile = self._update_profile(
            user_id, f"做了{topic}的题目，正确率{correct_rate}",
            behavior={"correct_rate": correct_rate, "duration": duration}
        )
        path_data = self._call_plan_agent(user_id, profile)
        resources = self._call_source_agent(profile, path_data)
        recommended = self._extract_recommended(resources)

        return {
            "profile": profile,
            "learning_path": path_data.get("path_list", []),
            "recommended_resources": recommended,
            "topic": profile.get("progress", {}).get("current_topic", ""),
            "current_progress": path_data.get("current_progress", "")
        }

    # ==================== 内部方法 ====================

    def _update_profile(self, user_id: str, message: str, behavior: Dict = None) -> Dict:
        resp = self.profile_agent.build_profile(user_id=user_id, user_input=message, behavior=behavior)
        # ✅ 保存后立刻转成字典返回给前端
        return resp.profile.model_dump()

    def _get_profile_dict(self, user_id: str) -> Dict:
        # 优先从内存/磁盘直接获取 Pydantic 对象转为字典
        profile = self.profile_agent.get_profile(user_id)
        if not profile:
            profile = self.profile_agent.load_profile_from_disk(user_id)
            if profile:
                self.profile_agent.profiles[user_id] = profile
        return profile.model_dump() if profile else {}

    def _call_plan_agent(self, user_id: str, profile: Dict) -> Dict:
        try:
            # 核心优化：不在当前目录读写文件，全部基于变量传递
            result = run_planner(memory_path=self.memory_path, user_profile=profile, output_dir=".")
            
            # 如果返回的是字典，直接处理
            if isinstance(result, dict):
                return self._process_plan_result(result, profile)
            
            # 兼容旧版（如果还是写的文件）
            result = {}
            if os.path.exists("learning_path.json"):
                with open("learning_path.json", "r", encoding="utf-8") as f:
                    lp = json.load(f)
                result["next"] = lp.get("next_step", "")
                result["current"] = lp.get("current_step") or profile.get("progress", {}).get("current_topic", "")
                
                review_flag = False
                if os.path.exists("teaching_output.json"):
                    with open("teaching_output.json", "r", encoding="utf-8") as f:
                      to = json.load(f)
                    review_flag = to.get("current_topic", {}).get("is_review", False)
                result["current_progress"] = "review" if review_flag else "learning"
                
                for node in lp.get("path_nodes", []):
                    if node.get("name") == result["current"]:
                        result["topic_id"] = node.get("id", "")
                        break
                result["path_list"] = lp.get("learning_path", [])[:5]
                result["module"] = profile.get("course", "")
            return result
        except Exception as e:
            print(f"⚠️ 路径规划失败: {e}")
            return {"current": "", "next": "", "current_progress": ""}

    def _process_plan_result(self, plan_data: Dict, profile: Dict) -> Dict:
        """处理新的路径规划返回结果"""
        result = {
            "next": plan_data.get("next_step", ""),
            "current": plan_data.get("current_step") or profile.get("progress", {}).get("current_topic", ""),
            "current_progress": "review" if plan_data.get("is_review", False) else "learning",
            "topic_id": plan_data.get("topic_id", ""),
            "path_list": plan_data.get("learning_path", [])[:5],
            "module": profile.get("course", "")
        }
        return result

    def _call_source_agent(self, profile: Dict, path_data: Dict) -> List[Dict]:
        resource_input = self._build_resource_input(profile, path_data)
        return self._call_source_agent_raw(resource_input)

    def _call_source_agent_raw(self, resource_input: Dict) -> Dict:
        try:
            result = generate_resources(resource_input)
            return result
        except Exception as e:
            print(f"⚠️ 资源生成失败: {e}")
            return {"resources": []}

    def _build_resource_input(self, profile: Dict, path_data: Optional[Dict]) -> Dict:
        return {
            "topic_id": path_data.get("topic_id", "") if path_data else "",
            "module": path_data.get("module", profile.get("course", "")) if path_data else profile.get("course", ""),
            "difficulty": profile.get("difficulty", "medium"),
            "learning_style": profile.get("learning_style", "text"),
            "weak_points": profile.get("weak_points", []),
            "understanding": self._get_current_understanding(profile),
            "current_progress": path_data.get("current_progress", "learning") if path_data else "learning",
            "resource_type": ["explanation"],
        }

    def _get_current_understanding(self, profile: Dict) -> float:
        current_topic = profile.get("progress", {}).get("current_topic", "")
        return profile.get("knowledge_level", {}).get(current_topic, 0.0)
    
    def _generate_reply(self, profile: Dict, path_data: Dict) -> str:
        weak = profile.get("weak_points", [])
        # 优先读取画像里最新的 current_topic
        current_topic = profile.get("progress", {}).get("current_topic", "")
        next_topic = path_data.get("next", "")
        
        # 1. 如果有薄弱点，优先聚焦薄弱点
        if weak:
            # 强行把当前学习主题置为第一个薄弱点，逻辑更通顺
            target = weak[0]
            # 如果路径规划里也有"下一个"，顺带提一句
            if next_topic and next_topic != target:
                return f"检测到你在「{target}」部分掌握较弱，建议优先攻克该知识点。攻克后可以继续学习「{next_topic}」。"
            return f"检测到你在「{target}」部分掌握较弱，建议集中复习该内容。"
        
        # 2. 没有薄弱点时，正常走学习路线
        elif current_topic:
            if next_topic:
                return f"当前已掌握「{current_topic}」，下一步建议学习「{next_topic}」。"
            return f"正在学习「{current_topic}」，请查看右侧推荐资源。"
            
        # 3. 兜底
        return "已为你更新学习计划，请查看推荐资源。"

    def _extract_recommended(self, resources) -> List[Dict]:
        if isinstance(resources, dict):
            resources = resources.get("resources", [])
        if not resources:
            return []
        return resources[:2]

    def _log_behavior(self, user_id: str, action: str, detail: str = "", duration: int = 0, correct_rate: float = None):
        self.behavior_log.append({
            "user_id": user_id, "action": action, "detail": detail,
            "duration": duration, "correct_rate": correct_rate,
            "timestamp": datetime.now().isoformat()
        })


_orchestrator = None

def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


def handle_chat(user_id: str, message: str, topic: str = None) -> Dict:
    return get_orchestrator().handle_chat(user_id, message, topic)

def get_learning_path(user_id: str, topic: str = None) -> Dict:
    return get_orchestrator().get_learning_path(user_id, topic)

def generate_single_resource(user_id: str, topic: str, resource_type: str) -> Dict:
    return get_orchestrator().generate_single_resource(user_id, topic, resource_type)

def finish_view_resource(user_id: str, resource_id: str, duration: int) -> Dict:
    return get_orchestrator().finish_view_resource(user_id, resource_id, duration)

def submit_answer_result(user_id: str, topic: str, correct_rate: float, duration: int) -> Dict:
    return get_orchestrator().submit_answer_result(user_id, topic, correct_rate, duration)