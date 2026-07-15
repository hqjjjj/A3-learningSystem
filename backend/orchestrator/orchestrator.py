# backend/orchestrator/orchestrator.py

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'behavior_system'))
from logger import log_behavior
from cleanup import cleanup_events
from analyzer import analyze_behavior

import json
from typing import Dict, Optional, List
from datetime import datetime
from functools import wraps
import time
import threading  # ✅ 新增

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

# 防抖装饰器（保留原有）
def debounce(wait_time):
    def decorator(func):
        last_called = {}

        @wraps(func)
        def debounced(*args, **kwargs):
            user_id = args[0]
            now = time.time()
            if user_id in last_called:
                if now - last_called[user_id] < wait_time:
                    print(f"【防抖】忽略用户 {user_id} 的重复调用，距离上次调用 {now - last_called[user_id]:.2f} 秒")
                    return {}
            last_called[user_id] = now
            return func(*args, **kwargs)
        return debounced
    return decorator

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
        # ✅ 防抖和缓存
        self._last_profile_update = {}   # user_id -> timestamp
        self._last_plan_cache = {}       # user_id -> (timestamp, result)
        self._plan_locks = {}            # user_id -> threading.Lock
        self._lock = threading.Lock()    # 保护 _plan_locks 的锁

    # ==================== 五个核心函数 ====================

    def handle_chat(self, user_id: str, message: str, topic: str = None) -> Dict:
        print(f"【总控】处理用户 {user_id} 的聊天消息: {message}")
        self._log_behavior(user_id, "chat", message)

        log_behavior(user_id, action="message", message=message)
        cleanup_events(user_id)

        # 1. 更新画像
        profile_dict = self._update_profile(user_id, message)

        if topic:
            print(f"【总控】设置用户 {user_id} 的当前主题为: {topic}")
            profile_obj = self.profile_agent.get_profile(user_id)
            if profile_obj:
                profile_obj.progress.current_topic = topic
                self.profile_agent._save_profile_to_disk(profile_obj)
                profile_dict = profile_obj.model_dump()

        # 2. 获取原始路径数据（包含 topic_id, module, path_list 等）
        raw_path_data = self._call_plan_agent(user_id, profile_dict)

        # 3. 意图识别，决定资源类型和回复风格
        intent = self._detect_intent(message)
        resource_types = ["explanation"]  # 默认

        if intent == "exercise":
            resource_types = ["exercise"]
            reply = f"好的！根据你当前的学习情况，我为你准备了一道关于「{raw_path_data.get('current', '')}」的练习题，请查看右侧资源区。"
        elif intent == "explain":
            resource_types = ["explanation", "mindmap"]
            reply = f"没问题！我来为你详细讲解「{raw_path_data.get('current', '')}」的核心概念，请查看右侧学习资源。"
        elif intent == "review":
            resource_types = ["explanation", "mindmap"]
            reply = f"好的，我们一起来回顾「{raw_path_data.get('current', '')}」的重点，帮助你巩固记忆。"
        else:
            reply = self._generate_reply(profile_dict, raw_path_data)

        # 兜底：确保 reply 不为空
        if not reply or reply.strip() == "":
            reply = "已收到你的消息，正在为你准备学习内容。"

        # 4. 生成资源（传入原始路径数据和资源类型）
        resources = self._call_source_agent(profile_dict, raw_path_data, user_id=user_id, resource_types=resource_types)
        recommended = self._extract_recommended(resources)

        return {
            "reply": reply,
            "profile": profile_dict,
            "learning_path": raw_path_data.get("path_list", []),
            "recommended_resources": recommended,
            "topic": profile_dict.get("progress", {}).get("current_topic", ""),
            "current_progress": raw_path_data.get("current_progress", "")
        }

    def get_learning_path(self, user_id: str, topic: str = None) -> Dict:
        print(f"【总控】获取用户 {user_id} 的学习路径")
        profile_obj = self.profile_agent.get_profile(user_id)
        if not profile_obj:
            print(f"【总控】从磁盘加载用户 {user_id} 的画像")
            profile_obj = self.profile_agent.load_profile_from_disk(user_id)
            if profile_obj:
                self.profile_agent.profiles[user_id] = profile_obj

        if not profile_obj:
            print(f"【总控】为用户 {user_id} 创建新画像")
            from profile_agent import StudentProfile
            profile_obj = StudentProfile(
                user_id=user_id,
                major="软件工程",
                grade="大二",
                course="操作系统",
                created_at=datetime.now()
            )
            self.profile_agent._save_profile_to_disk(profile_obj)
            self.profile_agent.profiles[user_id] = profile_obj

        if profile_obj and not profile_obj.progress.current_topic:
            print(f"【总控】用户没有当前主题，从知识库获取默认主题")
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'knowledge'))
                from KnowledgeBaseManager import KnowledgeBaseManager
                kb_manager = KnowledgeBaseManager()
                if len(kb_manager.topics_index) > 0:
                    first_id = list(kb_manager.topics_index.keys())[0]
                    first_topic = kb_manager.get_topic_by_id(first_id)
                    if first_topic:
                        profile_obj.progress.current_topic = first_topic.get("name", "")
                        self.profile_agent._save_profile_to_disk(profile_obj)
                        print(f"【总控】设置默认主题为: {profile_obj.progress.current_topic}")
            except Exception as e:
                print(f"【总控】⚠️ 设置默认主题失败: {e}")

        if topic and profile_obj:
            print(f"【总控】设置用户 {user_id} 的当前主题为: {topic}")
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
        print(f"【总控】为用户 {user_id} 生成 {topic} 的 {resource_type} 资源")
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

    @debounce(30)
    def finish_view_resource(self, user_id: str, resource_id: str, duration: int) -> Dict:
        print(f"【总控】用户 {user_id} 完成查看资源 {resource_id}，用时 {duration} 秒")
        self._log_behavior(user_id, "view_resource", f"resource:{resource_id}", duration)

        log_behavior(user_id, action="view_resource", resource_id=resource_id, duration=duration)
        cleanup_events(user_id)

        if duration >= 30:
            try:
                analyzed_data = analyze_behavior(user_id)
                print(f"【总控】分析用户 {user_id} 的行为数据")
            except Exception as e:
                print(f"【总控】⚠️ analyzer分析失败: {e}, 使用兜底数据")
                analyzed_data = {}
            profile = self._update_profile(
                user_id,
                f"仔细阅读了资源{resource_id}，用时{duration}秒",
                behavior=analyzed_data
            )
        else:
            profile = self._update_profile(user_id, f"浏览了资源{resource_id}，用时{duration}秒")

        path_data = self._call_plan_agent(user_id, profile)
        resources = self._call_source_agent(profile, path_data, user_id=user_id)
        recommended = self._extract_recommended(resources)

        return {
            "profile": profile,
            "learning_path": path_data.get("path_list", []),
            "recommended_resources": recommended,
            "topic": profile.get("progress", {}).get("current_topic", ""),
            "current_progress": path_data.get("current_progress", "")
        }

    @debounce(30)
    def submit_answer_result(self, user_id: str, topic: str, correct_rate: float, duration: int) -> Dict:
        print(f"【总控】用户 {user_id} 提交 {topic} 的答题结果，正确率: {correct_rate}，用时: {duration} 秒")
        self._log_behavior(user_id, "submit_answer", topic, duration, correct_rate)

        log_behavior(user_id, action="exercise", correct_rate=correct_rate, duration=duration)
        cleanup_events(user_id)

        try:
            analyzed_data = analyze_behavior(user_id)
            print(f"【总控】分析用户 {user_id} 的答题行为数据")
        except Exception as e:
            print(f"【总控】⚠️ analyzer分析失败: {e}, 使用兜底数据")
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
        # ✅ 防抖：5秒内重复调用则跳过
        now = time.time()
        if user_id in self._last_profile_update:
            if now - self._last_profile_update[user_id] < 5:
                print(f"【防抖】用户 {user_id} 画像更新过于频繁（间隔 {now - self._last_profile_update[user_id]:.1f}秒），跳过本次更新")
                return self._get_profile_dict(user_id)
        self._last_profile_update[user_id] = now

        print(f"【总控】开始更新用户 {user_id} 的画像")

        current_profile = self._get_profile_dict(user_id)
        if (current_profile.get("last_message") == message and
            current_profile.get("last_behavior") == behavior):
            print(f"【总控】用户 {user_id} 的画像无变化，跳过更新")
            return current_profile

        try:
            resp = self.profile_agent.build_profile(user_id=user_id, user_input=message, behavior=behavior)
            if resp and resp.profile:
                print(f"【总控】成功生成用户 {user_id} 的新画像")
                if resp.profile.major is None:
                    resp.profile.major = "软件工程"
                if resp.profile.grade is None:
                    resp.profile.grade = "大二"
                if resp.profile.course is None:
                    resp.profile.course = "操作系统"
                resp.profile.updated_at = datetime.now()
                resp.profile.last_message = message
                resp.profile.last_behavior = behavior

                try:
                    self.profile_agent._save_profile_to_disk(resp.profile)
                    print(f"【总控】成功保存用户 {user_id} 的画像到磁盘")
                    return resp.profile.model_dump()
                except Exception as e:
                    print(f"【总控】⚠️ 保存用户 {user_id} 画像到磁盘失败: {e}")
                    import traceback
                    traceback.print_exc()
                    return {}
            else:
                print(f"【总控】⚠️ 生成用户 {user_id} 画像失败")
                return {}
        except Exception as e:
            print(f"【总控】⚠️ 更新用户 {user_id} 画像时出错: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def _get_profile_dict(self, user_id: str) -> Dict:
        print(f"【总控】获取用户 {user_id} 的画像字典")
        profile = self.profile_agent.get_profile(user_id)
        if not profile:
            print(f"【总控】从磁盘加载用户 {user_id} 的画像")
            profile = self.profile_agent.load_profile_from_disk(user_id)
            if profile:
                self.profile_agent.profiles[user_id] = profile
        return profile.model_dump() if profile else {}

    def _call_plan_agent(self, user_id: str, profile: Dict) -> Dict:
        print(f"【调试】_call_plan_agent 被调用，user_id={user_id}")  # ✅ 添加这行
        # ✅ 获取或创建该用户的锁
        with self._lock:
            if user_id not in self._plan_locks:
                self._plan_locks[user_id] = threading.Lock()
            user_lock = self._plan_locks[user_id]

        # ✅ 使用锁保护路径规划
        with user_lock:
            # 双重检查：获取锁后再次检查缓存
            now = time.time()
            if user_id in self._last_plan_cache:
                cached_time, cached_result = self._last_plan_cache[user_id]
                if now - cached_time < 60:
                    print(f"【总控】路径规划缓存命中 (user={user_id})，间隔 {now - cached_time:.1f}秒")
                    return cached_result

            print(f"【总控】调用路径规划器，用户 {user_id}")
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(os.path.dirname(current_dir))
                knowledge_dir = os.path.join(project_root, "data", "knowledge")
                KNOWLEDGE_DIR = knowledge_dir

                print(f"【总控】知识库路径: {knowledge_dir}")

                current_topic_name = profile.get("progress", {}).get("current_topic", "")
                print(f"【总控】用户当前主题: {current_topic_name}")

                if not current_topic_name:
                    print(f"【总控】用户没有当前主题，设置默认主题")
                    sys.path.insert(0, os.path.join(current_dir, '..', '..', 'data', 'knowledge'))
                    from KnowledgeBaseManager import KnowledgeBaseManager
                    kb_manager = KnowledgeBaseManager()
                    if len(kb_manager.topics_index) > 0:
                        first_id = list(kb_manager.topics_index.keys())[0]
                        first_topic = kb_manager.get_topic_by_id(first_id)
                        if first_topic:
                            current_topic_name = first_topic.get("name", "")
                            profile["progress"]["current_topic"] = current_topic_name
                            print(f"【总控】设置默认主题为: {current_topic_name}")

                planner, updated_profile, next_topic, full_learning_path = run_planner(
                    KNOWLEDGE_DIR=KNOWLEDGE_DIR,
                    user_profile=profile,
                    output_dir=os.path.join(project_root, "data", "planner")
                )

                current_topic_name = profile.get("progress", {}).get("current_topic", "")
                current_topic_id = planner.kg.name_to_id.get(current_topic_name)

                if full_learning_path and "learning_path" in full_learning_path:
                    llm_path_names = full_learning_path.get("learning_path", [])
                    path_list = []
                    for name in llm_path_names:
                        topic_id = planner.kg.name_to_id.get(name)
                        if topic_id:
                            path_list.append({"name": name, "id": topic_id})

                    if path_list and current_topic_name:
                        current_in_path = any(p["name"] == current_topic_name for p in path_list)
                        if not current_in_path and current_topic_id:
                            path_list.insert(0, {"name": current_topic_name, "id": current_topic_id})

                    next_topic_name = ""
                    for i, item in enumerate(path_list):
                        if item["name"] == current_topic_name and i + 1 < len(path_list):
                            next_topic_name = path_list[i + 1]["name"]
                            break
                    if not next_topic_name and path_list:
                        next_topic_name = path_list[0]["name"]

                    MAX_PATH_LENGTH = 10
                    if len(path_list) > MAX_PATH_LENGTH:
                        path_list = path_list[:MAX_PATH_LENGTH]
                        print(f"【总控】路径过长，截断为 {MAX_PATH_LENGTH} 个节点")

                    result = {
                        "next": next_topic_name,
                        "current": current_topic_name,
                        "current_progress": "review" if current_topic_name in profile.get("weak_points", []) else "learning",
                        "topic_id": current_topic_id or (path_list[0]["id"] if path_list else ""),
                        "path_list": path_list,
                        "module": profile.get("course", "")
                    }

                    print(f"【总控】LLM 路径规划结果: {result}")
                    print(f"【总控】最终 path_list 长度: {len(path_list)}")
                    print(f"【总控】最终 path_list 内容: {path_list}")

                    self._last_plan_cache[user_id] = (now, result)
                    return result
                else:
                    print("【总控】LLM 路径为空，使用规则兜底")
                    result = {
                        "next": "",
                        "current": current_topic_name,
                        "current_progress": "learning",
                        "topic_id": "",
                        "path_list": [],
                        "module": profile.get("course", "")
                    }
                    self._last_plan_cache[user_id] = (now, result)
                    return result

            except Exception as e:
                print(f"【总控】⚠️ 路径规划失败: {e}")
                import traceback
                traceback.print_exc()
                result = {
                    "next": "",
                    "current": profile.get("progress", {}).get("current_topic", ""),
                    "current_progress": "learning",
                    "topic_id": "",
                    "path_list": [],
                    "module": profile.get("course", "")
                }
                return result

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

    def _call_source_agent(self, profile: Dict, path_data: Dict, user_id: str = None, resource_types: List[str] = None) -> List[Dict]:
        resource_input = self._build_resource_input(profile, path_data, resource_types)
        if user_id:
            resource_input["user_id"] = user_id
        return self._call_source_agent_raw(resource_input)

    def _call_source_agent_raw(self, resource_input: Dict) -> Dict:
        try:
            result = generate_resources(resource_input)
            return result
        except Exception as e:
            print(f"【总控】⚠️ 资源生成失败: {e}")
            return {"resources": []}

    def _build_resource_input(self, profile: Dict, path_data: Optional[Dict], resource_types: List[str] = None) -> Dict:
        if resource_types is None:
            resource_types = ["explanation"]
        return {
            "topic_id": path_data.get("topic_id", "") if path_data else "",
            "module": path_data.get("module", profile.get("course", "")) if path_data else profile.get("course", ""),
            "difficulty": profile.get("difficulty", "medium"),
            "learning_style": profile.get("learning_style", "text"),
            "weak_points": profile.get("weak_points", []),
            "understanding": self._get_current_understanding(profile),
            "current_progress": path_data.get("current_progress", "learning") if path_data else "learning",
            "resource_type": resource_types,
        }

    def _get_current_understanding(self, profile: Dict) -> float:
        current_topic = profile.get("progress", {}).get("current_topic", "")
        return profile.get("knowledge_level", {}).get(current_topic, 0.0)

    def _detect_intent(self, message: str) -> str:
        msg = message.lower()
        if any(k in msg for k in ["练习", "题目", "做题", "刷题", "习题", "测验", "测试", "考考"]):
            return "exercise"
        elif any(k in msg for k in ["讲解", "解释", "什么是", "概念", "讲一下", "介绍一下"]):
            return "explain"
        elif any(k in msg for k in ["复习", "回顾", "总结", "梳理", "巩固"]):
            return "review"
        else:
            return "general"

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

    # ==================== 用户登录/刷新加载方法 ====================
    def load_user_state(self, user_id: str) -> Dict:
        print(f"【总控】加载用户 {user_id} 的状态")
        try:
            profile_obj = self.profile_agent.get_profile(user_id)
            if not profile_obj:
                print(f"【总控】从磁盘加载用户 {user_id} 的画像")
                profile_obj = self.profile_agent.load_profile_from_disk(user_id)
                if profile_obj:
                    self.profile_agent.profiles[user_id] = profile_obj

            if not profile_obj:
                print(f"【总控】为用户 {user_id} 创建新画像")
                from profile_agent import StudentProfile
                profile_obj = StudentProfile(
                    user_id=user_id,
                    major="软件工程",
                    grade="大二",
                    course="操作系统",
                    created_at=datetime.now()
                )
                self.profile_agent._save_profile_to_disk(profile_obj)
                self.profile_agent.profiles[user_id] = profile_obj
            else:
                if profile_obj.major is None:
                    profile_obj.major = "软件工程"
                if profile_obj.grade is None:
                    profile_obj.grade = "大二"
                if profile_obj.course is None:
                    profile_obj.course = "操作系统"
                self.profile_agent._save_profile_to_disk(profile_obj)
                self.profile_agent.profiles[user_id] = profile_obj

            profile_dict = profile_obj.model_dump()
            print(f"【总控】用户 {user_id} 的画像: {profile_dict}")

            try:
                profile_dict = profile_obj.model_dump() if profile_obj else {}
                raw_path_data = self._call_plan_agent(user_id, profile_dict)
                print(f"【总控】原始路径数据: {raw_path_data}")
            except Exception as e:
                print(f"【总控】⚠️ 获取学习路径失败: {e}")
                raw_path_data = {
                    "next": "",
                    "current": "",
                    "path_list": [],
                    "current_progress": "learning",
                    "topic_id": ""
                }

            resources = {}
            try:
                if raw_path_data.get("topic_id"):
                    resources = self._call_source_agent(profile_dict, raw_path_data, user_id=user_id)
            except Exception as e:
                print(f"【总控】⚠️ 生成资源失败: {e}")
                import traceback
                traceback.print_exc()
                resources = {"resources": []}

            recommended = self._extract_recommended(resources)

            return {
                "profile": profile_dict,
                "learning_path": {
                    "current": raw_path_data.get("current", ""),
                    "next": raw_path_data.get("next", ""),
                    "path_list": raw_path_data.get("path_list", [])
                },
                "recommended_resources": recommended,
                "topic": profile_dict.get("progress", {}).get("current_topic", ""),
                "current_progress": raw_path_data.get("current_progress", "learning")
            }

        except Exception as e:
            print(f"【总控】⚠️ 加载用户状态失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "profile": {
                    "user_id": user_id,
                    "major": "软件工程",
                    "grade": "大二",
                    "course": "操作系统",
                    "knowledge_level": {},
                    "weak_points": [],
                    "error_tags": [],
                    "learning_style": "text",
                    "cognitive_style": {"visual": 0.33, "textual": 0.34, "auditory": 0.33},
                    "learning_pace": "normal",
                    "resource_type": ["explanation"],
                    "difficulty": "medium",
                    "progress": {"current_topic": "", "completed_topics": []},
                    "learning_goal": None,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                "learning_path": [],
                "recommended_resources": [],
                "topic": "",
                "current_progress": "learning"
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