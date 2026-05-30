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
        profile = self._update_profile(user_id, message)
        if topic:
            profile["progress"]["current_topic"] = topic
        path_data = self._call_plan_agent(user_id, profile)
        resources = self._call_source_agent(profile, path_data)
        reply = self._generate_reply(profile, path_data)
        recommended = self._extract_recommended(resources)

        return {
            "reply": reply,
            "profile": profile,
            "learning_path": path_data.get("path_list", []),
            "recommended_resources": recommended,
            "topic": profile.get("progress", {}).get("current_topic", ""),
            "current_progress": path_data.get("current_progress", "")
        }

    def get_learning_path(self, user_id: str, topic: str = None) -> Dict:
        profile = self._get_profile_dict(user_id)
        path_data = self._call_plan_agent(user_id, profile)
        return {
            "profile": profile,
            "learning_path": path_data.get("path_list", []),
            "topic": profile.get("progress", {}).get("current_topic", ""),
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
        return resp.profile.model_dump()

    def _get_profile_dict(self, user_id: str) -> Dict:
        profile = self.profile_agent.get_profile(user_id)
        return profile.model_dump() if profile else {}

    def _call_plan_agent(self, user_id: str, profile: Dict) -> Dict:
        try:
            run_planner(memory_path=self.memory_path, user_profile=profile, output_dir=".")
            result = {}
            if os.path.exists("learning_path.json"):
                with open("learning_path.json", "r", encoding="utf-8") as f:
                    lp = json.load(f)
                # next_step 从文件取
                result["next"] = lp.get("next_step", "")
                # current 优先取文件，文件为 None 则取画像的 current_topic
                result["current"] = lp.get("current_step") or profile.get("progress", {}).get("current_topic", "")
                # 从 teaching_output.json 读取 is_review
                review_flag = False
                if os.path.exists("teaching_output.json"):
                    with open("teaching_output.json", "r", encoding="utf-8") as f:
                      to = json.load(f)
                    review_flag = to.get("current_topic", {}).get("is_review", False)
                result["current_progress"] = "review" if review_flag else "learning"
                # topic_id 从 path_nodes 中匹配
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

    def _call_source_agent(self, profile: Dict, path_data: Dict) -> List[Dict]:
        resource_input = self._build_resource_input(profile, path_data)
        return self._call_source_agent_raw(resource_input)

    def _call_source_agent_raw(self, resource_input: Dict) -> Dict:
        try:
            result = {}
            topic_id = resource_input.get("topic_id", "")
            resource_types = resource_input.get("resource_type", [])

            # 将 topic_id 转为完整的 topic 字典（队友C需要）
            topic = self._get_topic_by_id(topic_id)
            if topic is None:
                print(f"⚠️ 未找到知识点: {topic_id}")
                return {"resources": []}

            if "code_example" in resource_types:
                try:
                    result.update(self.code_agent.run(resource_input, topic))
                except Exception as e:
                    print(f"⚠️ code_agent失败: {e}")
            if "exercise" in resource_types:
                try:
                    result.update(self.exercise_agent.run(resource_input, topic))
                except Exception as e:
                    print(f"⚠️ exercise_agent失败: {e}")
            if any(t in resource_types for t in ["explanation", "mindmap", "materials"]):
                try:
                    result.update(self.kn_agent.run(resource_input, topic, resource_types))
                except Exception as e:
                    print(f"⚠️ kn_agent失败: {e}")

            resources = []
            for key, value in result.items():
                if isinstance(value, dict):
                    value.setdefault("type", key)
                    resources.append(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            item.setdefault("type", key)
                            resources.append(item)
            return {"resources": resources}
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
        }

    def _get_current_understanding(self, profile: Dict) -> float:
        current_topic = profile.get("progress", {}).get("current_topic", "")
        return profile.get("knowledge_level", {}).get(current_topic, 0.0)
    
    def _get_topic_by_id(self, topic_id: str) -> Optional[Dict]:
        """根据 topic_id 从知识图谱中获取完整的 topic 字典"""
        import json as _json
        memory_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'data', 'knowledge', 'memory.json'
        )
        try:
            with open(memory_path, 'r', encoding='utf-8') as f:
                data = _json.load(f)
            for topic in data.get('topics', []):
                if topic.get('id') == topic_id:
                    return topic
        except Exception as e:
            print(f"⚠️ 读取知识图谱失败: {e}")
        return None

    def _generate_reply(self, profile: Dict, path_data: Dict) -> str:
        weak = profile.get("weak_points", [])
        current = path_data.get("current", "")
        next_topic = path_data.get("next", "")
        if weak:
            return f"检测到你在{'、'.join(weak)}部分掌握较弱，建议先复习{current}，再学习{next_topic}。"
        elif next_topic:
            return f"当前学习{current}，下一步建议学习{next_topic}。"
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