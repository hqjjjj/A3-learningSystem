# backend/orchestrator/orchestrator.py

# 导入行为系统
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'behavior_system'))
from logger import log_behavior
from cleanup import cleanup_events
from analyzer import analyze_behavior


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
            os.path.dirname(__file__), '..', '..', 'data', 'knowledge'
        )

    # ==================== 五个核心函数 ====================

    def handle_chat(self, user_id: str, message: str, topic: str = None) -> Dict:
        self._log_behavior(user_id, "chat", message)
        
        log_behavior(user_id, action="message", message=message)
        cleanup_events(user_id)
        
        profile_dict = self._update_profile(user_id, message)
        
        if topic:
            profile_obj = self.profile_agent.get_profile(user_id)
            if profile_obj:
                profile_obj.progress.current_topic = topic
                self.profile_agent._save_profile_to_disk(profile_obj)
                profile_dict = profile_obj.model_dump()
        
        path_data = self.get_learning_path(user_id, topic) 
        resources = self._call_source_agent(profile_dict, path_data)
        reply = self._generate_reply(profile_dict, path_data)
        recommended = self._extract_recommended(resources)

        return {
            "reply": reply,
            "profile": profile_dict, 
            "learning_path": path_data.get("path_list", []),
            "recommended_resources": recommended,
            "topic": profile_dict.get("progress", {}).get("current_topic", ""),
            "current_progress": path_data.get("current_progress", "")
        }

    def get_learning_path(self, user_id: str, topic: str = None) -> Dict:
        profile_obj = self.profile_agent.get_profile(user_id)
        
        if not profile_obj:
            profile_obj = self.profile_agent.load_profile_from_disk(user_id)
            if profile_obj:
                self.profile_agent.profiles[user_id] = profile_obj

        if topic and profile_obj:
            profile_obj.progress.current_topic = topic
            self.profile_agent._save_profile_to_disk(profile_obj)
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
        
        log_behavior(user_id, action="view_resource", resource_id=resource_id, duration=duration)
        cleanup_events(user_id)
        
        if duration >= 30:
            try:
                analyzed_data = analyze_behavior(user_id)
            except Exception as e:
                print(f"⚠️ analyzer分析失败: {e}, 使用兜底数据")
                analyzed_data = {}
                
            profile = self._update_profile(
                user_id, 
                f"仔细阅读了资源{resource_id}，用时{duration}秒", 
                behavior=analyzed_data
            )
        else:
            profile = self._update_profile(user_id, f"浏览了资源{resource_id}，用时{duration}秒")
            
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
        
        log_behavior(user_id, action="exercise", correct_rate=correct_rate, duration=duration)
        cleanup_events(user_id)
        
        try:
            analyzed_data = analyze_behavior(user_id)
        except Exception as e:
            print(f"⚠️ analyzer分析失败: {e}, 使用兜底数据")
            analyzed_data = {"correct_rate": correct_rate}
        
        profile = self._update_profile(
            user_id, 
            f"做了{topic}的题目，正确率{correct_rate}，用时{duration}秒",
            behavior=analyzed_data
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
        if resp and resp.profile:
            self.profile_agent._save_profile_to_disk(resp.profile)
        return resp.profile.model_dump()

    def _get_profile_dict(self, user_id: str) -> Dict:
        profile = self.profile_agent.get_profile(user_id)
        if not profile:
            profile = self.profile_agent.load_profile_from_disk(user_id)
            if profile:
                self.profile_agent.profiles[user_id] = profile
        return profile.model_dump() if profile else {}

    def _call_plan_agent(self, user_id: str, profile: Dict) -> Dict:
        try:
            # 导入 KnowledgeBaseManager
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'knowledge'))
            from KnowledgeBaseManager import KnowledgeBaseManager
            
            kb_manager = KnowledgeBaseManager()
            
            # 1. 获取用户当前的主题
            current_topic_name = profile.get("progress", {}).get("current_topic", "")
            
            # ====================================================
            # 🔥 逻辑修正点：如果用户当前没有 Topic，或者 Topic 是空的，直接返回空路径！
            # 这样就不会出现“无限匹配空字符串”或者“无限匹配旧数据”的情况。
            # ====================================================
            if not current_topic_name:
                return {
                    "next": "",
                    "current": "",
                    "current_progress": "learning",
                    "topic_id": "",
                    "path_list": [],
                    "module": profile.get("course", "")
                }

            # 2. 真正的智能匹配：调用 KnowledgeBaseManager 的语义匹配
            # 如果你用了我的上一版代码，在这里会打印 "🔎 正在匹配: ..."
            matched_topic = kb_manager.match_and_get(current_topic_name)
            
            # 3. 兜底：如果匹配不到，给你一个默认的（防止界面空转）
            if not matched_topic and len(kb_manager.topics_index) > 0:
                # 取第一个知识点作为默认起点
                first_id = list(kb_manager.topics_index.keys())[0]
                matched_topic = kb_manager.get_topic_by_id(first_id)
            
            # 4. 构造返回结果
            result = {
                "next": "",
                "current": matched_topic.get("name", "") if matched_topic else "",
                "current_progress": "learning",
                "topic_id": matched_topic.get("id", "") if matched_topic else "",
                "path_list": [],  # 这里目前为空，因为路径规划在下一步做
                "module": profile.get("course", "")
            }
            
            return result
            
        except Exception as e:
            print(f"⚠️ 知识库匹配与规划失败: {e}")
            return {"current": "", "next": "", "current_progress": ""}

    def _process_plan_result(self, plan_data: Dict, profile: Dict) -> Dict:
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
        current_topic = profile.get("progress", {}).get("current_topic", "")
        next_topic = path_data.get("next", "")
        if weak:
            weak_str = "、".join(weak)
            if next_topic:
                return f"检测到你在「{weak_str}」部分掌握较弱。建议优先集中攻克这些薄弱点，再继续学习「{next_topic}」。"
            return f"检测到你在「{weak_str}」部分掌握较弱，建议集中复习，巩固基础。"
        elif current_topic:
            if next_topic:
                return f"当前已掌握「{current_topic}」，下一步建议学习「{next_topic}」。"
            return f"正在学习「{current_topic}」，请查看右侧推荐资源。"
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

    # ==================== 新增：用户登录/刷新加载方法 ====================
    def load_user_state(self, user_id: str) -> Dict:
        """
        用户登录/页面刷新时调用，加载完整状态。
        返回的字典结构必须匹配前端期望的 data 对象。
        """
        # 1. 获取用户画像
        profile_obj = self.profile_agent.get_profile(user_id)
        if not profile_obj:
            profile_obj = self.profile_agent.load_profile_from_disk(user_id)
            if profile_obj:
                self.profile_agent.profiles[user_id] = profile_obj

        if not profile_obj:
            # 从 ProfileAgent 里借用 StudentProfile，避免 ImportError
            from profile_agent import StudentProfile
            empty_profile = StudentProfile(user_id=user_id, created_at=datetime.now())
            self.profile_agent.profiles[user_id] = empty_profile
            profile_obj = empty_profile

        profile_dict = profile_obj.model_dump()
        
        # 2. 获取学习路径
        path_data = self.get_learning_path(user_id)
        
        # 3. 根据目前的画像和路径，推荐首批资源（如果有学习路径的话）
        resources = {}
        if path_data.get("topic_id"):
            resources = self._call_source_agent(profile_dict, path_data)
        recommended = self._extract_recommended(resources)

        return {
            "profile": profile_dict,
            "learning_path": path_data.get("path_list", []),
            "recommended_resources": recommended,
            "topic": profile_dict.get("progress", {}).get("current_topic", ""),
            "current_progress": path_data.get("current_progress", "learning")
        }


# ============= 全局函数导出入口 =============
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

def load_user_state(user_id: str) -> Dict:
    return get_orchestrator().load_user_state(user_id)

def load_user_state(user_id: str) -> Dict:
    return get_orchestrator().load_user_state(user_id)