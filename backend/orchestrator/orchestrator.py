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
            os.path.dirname(__file__), '..', '..', 'data', 'knowledge', 'memory.json'
        )

    # ==================== 五个核心函数 ====================

    def handle_chat(self, user_id: str, message: str, topic: str = None) -> Dict:
        self._log_behavior(user_id, "chat", message)
        
        # 普通聊天，只记录到事件文件，不触发 analyzer
        log_behavior(user_id, action="message", message=message)
        cleanup_events(user_id)
        
        # ... (后续的 画像更新、路径规划、资源生成 代码保持不变) ...
        
        # 1. 更新画像（此时已处理用户消息，写入了新的薄弱点）
        profile_dict = self._update_profile(user_id, message)
        
        # 2. 如果前端明确指定了 Topic，强制更新画像对象的 current_topic
        if topic:
            profile_obj = self.profile_agent.get_profile(user_id)
            if profile_obj:
                profile_obj.progress.current_topic = topic
                # 强制同步到磁盘
                self.profile_agent._save_profile_to_disk(profile_obj)
                profile_dict = profile_obj.model_dump()
        
        # 3. 【关键修复】规划路径：强制调用 get_learning_path，让总控基于最新画像重新计算路径和ID
        # 这样能确保路径规划器拿到最新的状态，而非旧状态
        path_data = self.get_learning_path(user_id, topic) 
        
        # 4. 生成资源（此时使用的是最新的、正确的 path_data）
        resources = self._call_source_agent(profile_dict, path_data)
        
        # 5. 生成回复
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
        
        # 如果内存里没有，尝试从磁盘加载
        if not profile_obj:
            profile_obj = self.profile_agent.load_profile_from_disk(user_id)
            if profile_obj:
                self.profile_agent.profiles[user_id] = profile_obj

        # 如果 get_learning_path 收到了 topic 参数，强行写入画像对象！
        if topic and profile_obj:
            profile_obj.progress.current_topic = topic
            # 既然手动改了主题，同步写入磁盘
            self.profile_agent._save_profile_to_disk(profile_obj)
            # 更新缓存的字典
            self.profile_agent.profiles[user_id] = profile_obj

        profile_dict = profile_obj.model_dump() if profile_obj else {}
        
        # ========== 重点优化：重新根据最新画像调用路径规划 ==========
        path_data = self._call_plan_agent(user_id, profile_dict)
        # ==========================================================
        
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
        
        # 触发行为系统：日志记录
        log_behavior(user_id, action="view_resource", resource_id=resource_id, duration=duration)
        cleanup_events(user_id) # 维护窗口
        
        # 如果浏览时间超过某个阈值（比如 30秒），认为是深入学习，触发 analyzer
        if duration >= 30:
            # 调用 analyzer，它会返回统计后的画像参数
            analyzed_data = analyze_behavior(user_id)
            
            # 将 analyze 的结果作为 behavior 传进去，与消息一起更新画像
            profile = self._update_profile(
                user_id, 
                f"仔细阅读了资源{resource_id}，用时{duration}秒", 
                behavior=analyzed_data # 将行为统计结果传给 LLM/画像更新
            )
        else:
            # 只是简单浏览，只更新对话记录
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
        
        # 触发行为系统：记录做题事件
        log_behavior(user_id, action="exercise", correct_rate=correct_rate, duration=duration)
        cleanup_events(user_id) # 维护窗口
        
        # 练习动作必须触发 analyzer，计算最新的掌握度
        analyzed_data = analyze_behavior(user_id)
        
        # 将 analyzer 分析出的掌握度数据传给 ProfileAgent
        # 注意：这里 behavior 不仅仅是 correct_rate 了，而是 analyzer 返回的完整字典
        profile = self._update_profile(
            user_id, 
            f"做了{topic}的题目，正确率{correct_rate}，用时{duration}秒",
            behavior=analyzed_data # 把统计结果传进去
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
        # [修复点 1] build_profile 内部其实已经自己存了盘，但为了稳妥，我们再显式写一次
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
        current_topic = profile.get("progress", {}).get("current_topic", "")
        next_topic = path_data.get("next", "")
        if weak:
            # 1. 把所有薄弱点用顿号连起来，显得系统很聪明
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


_orchestrator = None

def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


def load_user_state(self, user_id: str) -> Dict:
        """
        用户登录/页面刷新时调用，加载完整状态。
        返回的字典结构必须完全匹配前端截图中的 data 对象。
        """
        # 1. 获取用户的画像（从内存读，不存在则从磁盘加载，并写入内存）
        profile_obj = self.profile_agent.get_profile(user_id)
        if not profile_obj:
            profile_obj = self.profile_agent.load_profile_from_disk(user_id)
            if profile_obj:
                self.profile_agent.profiles[user_id] = profile_obj
        
        # 如果完全没有该用户的数据，创建一个空的兜底对象
        if not profile_obj:
            empty_profile = StudentProfile(user_id=user_id, created_at=datetime.now())
            self.profile_agent.profiles[user_id] = empty_profile
            profile_obj = empty_profile

        profile_dict = profile_obj.model_dump()
        
        # 2. 获取学习路径
        # 注意：这里调用 get_learning_path 会自动加载并返回最新的路径数据
        path_data = self.get_learning_path(user_id)
        
        # 3. 根据目前的画像和路径，推荐首批资源（如果有学习路径的话）
        # 注意：这里我们复用 `_call_source_agent` 来获取推荐资源
        resources = {}
        if path_data.get("topic_id"):
            resources = self._call_source_agent(profile_dict, path_data)
        
        recommended = self._extract_recommended(resources)

        # 4. 组装返回给前端的数据
        return {
            "user_id": user_id,
            "profile": profile_dict,
            "learning_path": path_data.get("path_list", []),
            "recommended_resources": recommended,
            "topic": profile_dict.get("progress", {}).get("current_topic", ""),
            "current_progress": path_data.get("current_progress", "learning")
        }

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