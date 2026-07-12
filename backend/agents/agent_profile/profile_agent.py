import requests
import json
import datetime
import os
import re
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

os.environ["no_proxy"] = "*"

# ============================================
# 数据模型定义
# ============================================
class CognitiveStyle(BaseModel):
    visual: float = 0.33
    textual: float = 0.33
    auditory: float = 0.34

class Progress(BaseModel):
    current_topic: Optional[str] = None
    completed_topics: List[str] = []

class StudentProfile(BaseModel):
    user_id: str
    major: Optional[str] = None
    grade: Optional[str] = None
    course: Optional[str] = None
    knowledge_level: Dict[str, float] = Field(default_factory=dict)
    weak_points: List[str] = Field(default_factory=list)
    error_tags: List[str] = Field(default_factory=list)
    learning_style: str = "text"
    cognitive_style: CognitiveStyle = Field(default_factory=CognitiveStyle)
    learning_pace: str = "normal"
    resource_type: List[str] = Field(default_factory=lambda: ["explanation"])
    difficulty: str = "medium"
    progress: Progress = Field(default_factory=Progress)
    learning_goal: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    
    # ✅ 新增：用于防抖检查的字段
    last_message: Optional[str] = None
    last_behavior: Optional[dict] = None

class ProfileResponse(BaseModel):
    profile: StudentProfile
    update_type: str
    confidence: float
# ============================================

# ============ 加载课程知识图谱（支持多文件合并） ============
KNOWLEDGE_GRAPH = {}
try:
    agent_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(agent_dir)))
    
    knowledge_dir = os.path.join(project_root, "data", "knowledge")
    total_topics = 0
    
    if os.path.exists(knowledge_dir):
        for filename in os.listdir(knowledge_dir):
            if filename.endswith(".json") and filename != "__init__.py":
                file_path = os.path.join(knowledge_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if "topics" in data:
                            for topic in data["topics"]:
                                KNOWLEDGE_GRAPH[topic["name"]] = topic
                                total_topics += 1
                    print(f"📖 已加载: {filename}")
                except Exception as e:
                    print(f"【画像Agent】⚠️ 读取 {filename} 失败: {e}")
                    
    print(f"【画像Agent】✅ 成功加载 {len(KNOWLEDGE_GRAPH)} 个课程知识点 (涵盖 12 个章节)")
except Exception as e:
    print(f"【画像Agent】⚠️ 遍历 knowledge 目录失败: {e}")


class ProfileAgent:
    """学习画像构建智能体"""

    def __init__(self, api_password: str = None):
        # 🔥 根据官方文档修正配置
        self.api_password = api_password or "wgBxAZOFHyntyLUcGyiA:nOjHYLiHrgAffNqWCcUJ"  # 你的APIPassword
        self.base_url = "https://spark-api-open.xf-yun.com/agent/v1/chat/completions"
        self.model = "spark-x"  # 🔥 关键修正：X2-flash版本对应的model必须填 "spark-x"
        
        self.profiles: Dict[str, StudentProfile] = {}
        
        agent_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(agent_dir)))
        self.data_root = os.path.join(project_root, "data", "profile_outputs")
        os.makedirs(self.data_root, exist_ok=True)
        
        self._load_all_profiles()

    def _call_llm(self, system_prompt: str, user_msg: str) -> dict:
        """调用讯飞 Spark-X2-Flash API"""
        headers = {
            "Authorization": f"Bearer {self.api_password}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
            "stream": False  # 使用非流式请求
        }

        max_retries = 2
        for attempt in range(max_retries):
            try:
                resp = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
                result = resp.json()

                # 🔥 根据文档，code为0表示成功
                if result.get("code") == 0 and "choices" in result and len(result["choices"]) > 0:
                    msg = result["choices"][0].get("message", {})
                    content = msg.get("content", "").strip()
                    
                    # 🔥 兼容深度思考模型：如果content为空，尝试从reasoning_content中提取
                    if not content:
                        reasoning = msg.get("reasoning_content", "")
                        start = reasoning.rfind('{')
                        end = reasoning.rfind('}')
                        if start != -1 and end != -1 and end > start:
                            content = reasoning[start:end+1]
                            
                    if not content:
                        if attempt < max_retries - 1:
                            continue
                        return {}

                    # ======================= 核心清理区 =======================
                    # 1. 去除 Markdown 代码块包裹
                    if content.startswith("```"):
                        lines = content.split('\n')
                        content = '\n'.join(lines[1:]) if len(lines) > 1 else content
                        if content.endswith("```"):
                            content = content[:-3]

                    content = content.strip()
                    
                    # 2. 修复常见的 JSON 格式错误
                    content = re.sub(r',\s*}', '}', content)
                    content = re.sub(r',\s*]', ']', content)
                    content = re.sub(r'(?<!\\)\n', '\\n', content)

                    # 3. 解析JSON
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        start_brace = content.find('{')
                        end_brace = content.rfind('}')
                        if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
                            json_str = content[start_brace : end_brace + 1]
                            try:
                                return json.loads(json_str)
                            except:
                                raise
                        else:
                            raise
                    # ===========================================================
                else:
                    error_msg = result.get("message", json.dumps(result, ensure_ascii=False))
                    if attempt < max_retries - 1:
                        continue
                    raise Exception(f"API调用失败: {result}")
            except json.JSONDecodeError:
                if attempt < max_retries - 1:
                    continue
                raise
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    continue
                raise
            except Exception as e:
                print(f"【画像Agent】LLM请求异常: {e}")
                if attempt < max_retries - 1:
                    continue
                raise

        raise Exception("API调用失败，已达最大重试次数")

    # ================= 其他方法保持不变 =================
    def _match_topic_locally(self, user_input: str) -> Optional[str]:
        if not user_input:
            return None
        user_input = user_input.strip()
        for topic_name in KNOWLEDGE_GRAPH.keys():
            if topic_name in user_input:
                return topic_name
        return None

    def _load_all_profiles(self):
        try:
            if os.path.exists(self.data_root):
                profile_files = [f for f in os.listdir(self.data_root) if f.endswith('.json')]
                for filename in profile_files:
                    try:
                        user_id = filename.replace('profile_', '').replace('.json', '')
                        profile = self.load_profile_from_disk(user_id)
                        if profile:
                            self.profiles[user_id] = profile
                    except Exception as e:
                        print(f"【画像Agent】⚠️ 加载画像失败 {filename}: {e}")
                print(f"【画像Agent】✅ 已加载 {len(self.profiles)} 个用户画像")
        except Exception as e:
            print(f"【画像Agent】⚠️ 加载用户画像目录失败: {e}")

    def _save_profile_to_disk(self, profile: StudentProfile):
        self.profiles[profile.user_id] = profile
        file_path = os.path.join(self.data_root, f"profile_{profile.user_id}.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(profile.model_dump_json(indent=2))
            print(f"【画像Agent】✅ 用户 {profile.user_id} 画像已保存到本地")
        except Exception as e:
            print(f"【画像Agent】⚠️ 保存用户 {profile.user_id} 本地画像失败: {e}")

    def load_profile_from_disk(self, user_id: str) -> Optional[StudentProfile]:
        file_path = os.path.join(self.data_root, f"profile_{user_id}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    profile = StudentProfile.model_validate(data)
                    self._ensure_basic_info(profile)
                    return profile
            except Exception as e:
                print(f"【画像Agent】⚠️ 读取用户 {user_id} 历史画像失败: {e}")
        return None

    def _ensure_basic_info(self, profile: StudentProfile):
        if profile.major is None:
            profile.major = "软件工程"
        if profile.grade is None:
            profile.grade = "大二"
        if profile.course is None:
            profile.course = "操作系统"

    def build_profile(self, user_id: str, user_input: str,
                      history: List[dict] = None,
                      behavior: dict = None) -> ProfileResponse:
        print(f"【画像Agent】开始构建用户 {user_id} 的画像")
        old_profile = self.profiles.get(user_id)
        
        if not old_profile:
            old_profile = self.load_profile_from_disk(user_id)
            if old_profile:
                self.profiles[user_id] = old_profile

        # ✅ 优化：只发送相关知识点，而不是整个知识图谱
        relevant_topics = set() # 使用集合去重
        
        # 1. 从旧画像中获取当前主题
        if old_profile and old_profile.progress.current_topic:
            current_topic = old_profile.progress.current_topic
            if current_topic in KNOWLEDGE_GRAPH:
                relevant_topics.add(current_topic)
        
        # 2. 从用户输入中匹配主题
        matched_topic = self._match_topic_locally(user_input)
        if matched_topic:
            relevant_topics.add(matched_topic)
            
        # 3. 从行为数据中获取主题（如果有）
        if behavior and "topic" in behavior:
            topic_name = behavior["topic"]
            if topic_name in KNOWLEDGE_GRAPH:
                relevant_topics.add(topic_name)
        
        # 4. 兜底：如果筛选不到，取前5个
        if not relevant_topics:
            relevant_topics = set(list(KNOWLEDGE_GRAPH.keys())[:5])

        # 生成 topics_str
        topics_list = []
        for tname in relevant_topics:
            tdata = KNOWLEDGE_GRAPH[tname]
            topics_list.append(f"'{tname}' (难度: {tdata['difficulty']})")
        topics_str = "\n".join(topics_list)

        sys_prompt = f"""你是一个学习画像构建助手。分析学生的对话与行为数据，输出标准JSON。

## 可选知识点（名称必须完全一致）
{topics_str}

## 提取规则
1. major: 专业名称（如"计算机"），无法推断填null
2. grade: 年级（如"大三"），无法推断填null
3. course: 课程名称（如"操作系统"），无法推断填null
4. progress.current_topic: 学生当前正在学习或询问的知识点名称，必须从上面选
5. cognitive_style: {{"visual": 0.0, "textual": 0.0, "auditory": 0.0}}，三者和为1
   - 说"看视频/动画"→visual高0.6-0.7，其他各0.15-0.2
   - 说"看文档/看书"→textual高0.6-0.7，其他各0.15-0.2
   - 无明确偏好→三者均匀分配
6. learning_pace: "normal"/"slow"/"fast"，默认值为 "normal"。如果有明确证据表明学生学得很快（如"我学得很快"、"我提前学完了"）才改为 "fast"，有明确证据表明严重阻碍才改为 "slow"。
7. resource_type: 资源类型列表，从["explanation", "mindmap", "exercise", "code_example"]中选择。根据学生偏好和行为动态推断，如喜欢看视频→["explanation", "mindmap"]，做题正确率低→["explanation", "exercise"]
8. difficulty: "easy"/"medium"/"hard"
9. learning_goal: 无法推断填null

## 输出要求
必须是合法JSON，无说明文字，无markdown代码块包裹，直接输出纯JSON。"""
        
        user_message = f"学生输入：{user_input}\n行为数据：{json.dumps(behavior or {}, ensure_ascii=False)}\n旧画像：{old_profile.model_dump() if old_profile else '无'}"

        try:
            print(f"【画像Agent】尝试调用LLM更新用户 {user_id} 的画像")
            extraction = self._call_llm(sys_prompt, user_message)
            print(f"【画像Agent】LLM调用成功，开始更新用户 {user_id} 的画像")
        except Exception as e:
            print(f"【画像Agent】LLM调用失败，使用兜底数据: {e}")
            if old_profile:
                self._ensure_basic_info(old_profile)
                return ProfileResponse(profile=old_profile, update_type="update", confidence=0.3)
            profile = StudentProfile(user_id=user_id, created_at=datetime.datetime.now())
            self._ensure_basic_info(profile)
            for topic_name in KNOWLEDGE_GRAPH:
                profile.knowledge_level[topic_name] = 0.0
            update_type = "init"
        else:
            if not old_profile:
                profile = StudentProfile(user_id=user_id, created_at=datetime.datetime.now())
                for topic_name in KNOWLEDGE_GRAPH:
                    profile.knowledge_level[topic_name] = 0.0
                update_type = "init"
            else:
                profile = old_profile
                update_type = "update"

            if extraction.get("major"):
                profile.major = extraction["major"]
            if extraction.get("grade"):
                profile.grade = extraction["grade"]
            if extraction.get("course"):
                profile.course = extraction["course"]

            if "cognitive_style" in extraction:
                cs = extraction["cognitive_style"]
                total = cs.get("visual", 0) + cs.get("textual", 0) + cs.get("auditory", 0)
                if total > 0:
                    profile.cognitive_style = CognitiveStyle(
                        visual=round(cs.get("visual", 0) / total, 2),
                        textual=round(cs.get("textual", 0) / total, 2),
                        auditory=round(cs.get("auditory", 0) / total, 2)
                    )
            profile.learning_style = "diagram" if profile.cognitive_style.visual >= 0.5 else "text"

            if extraction.get("learning_pace"):
                profile.learning_pace = extraction["learning_pace"]

            if "resource_type" in extraction and isinstance(extraction["resource_type"], list):
                profile.resource_type = list(set(profile.resource_type + extraction["resource_type"]))
            if "difficulty" in extraction:
                profile.difficulty = extraction["difficulty"]

            matched_topic = None
            if "progress" in extraction and extraction["progress"].get("current_topic"):
                topic_name = extraction["progress"]["current_topic"]
                if topic_name in KNOWLEDGE_GRAPH:
                    matched_topic = KNOWLEDGE_GRAPH[topic_name]
                else:
                    matched_topic_name = self._match_topic_locally(topic_name)
                    if matched_topic_name:
                        matched_topic = KNOWLEDGE_GRAPH[matched_topic_name]

            if not matched_topic:
                matched_topic_name = self._match_topic_locally(user_input)
                if matched_topic_name:
                    matched_topic = KNOWLEDGE_GRAPH[matched_topic_name]

            if matched_topic:
                profile.progress.current_topic = matched_topic["name"]

            current_topic = profile.progress.current_topic
            correct_rate = behavior.get("correct_rate", None) if behavior else None

            if current_topic and current_topic in KNOWLEDGE_GRAPH:
                old_score = profile.knowledge_level.get(current_topic, 0.0)
                base_score = 0.45
                if correct_rate is not None:
                    if correct_rate < 0.4:
                        base_score = 0.25
                    elif correct_rate > 0.8:
                        base_score = 0.75
                if profile.learning_pace == "slow":
                    base_score = min(base_score, 0.4)
                elif profile.learning_pace == "fast":
                    base_score = max(base_score, 0.7)
                profile.knowledge_level[current_topic] = base_score if old_score == 0.0 else round(old_score * 0.7 + base_score * 0.3, 2)

            profile.weak_points = [name for name, score in profile.knowledge_level.items() if 0.0 < score < 0.6]
            profile.error_tags = [name for name, score in profile.knowledge_level.items() if 0.0 < score < 0.4]

            if user_input and user_input.strip() != "":
                for topic_name, score in profile.knowledge_level.items():
                    if topic_name in user_input and score < 0.6:
                        if topic_name not in profile.weak_points:
                            profile.weak_points.append(topic_name)
                        if score < 0.4 and topic_name not in profile.error_tags:
                            profile.error_tags.append(topic_name)

            if not profile.weak_points and len(profile.knowledge_level) > 0:
                sorted_topics = sorted(profile.knowledge_level.items(), key=lambda x: x[1])
                for topic_name, score in sorted_topics:
                    if score < 0.6 and score > 0.0:
                        profile.weak_points.append(topic_name)
                        if len(profile.weak_points) >= 3:
                            break

        self._ensure_basic_info(profile)
        profile.updated_at = datetime.datetime.now()
        
        # ✅ 更新 last_message 和 last_behavior 用于防抖
        profile.last_message = user_input
        profile.last_behavior = behavior
        
        self.profiles[user_id] = profile
        self._save_profile_to_disk(profile)
        
        print(f"【画像Agent】成功更新用户 {user_id} 的画像")
        return ProfileResponse(profile=profile, update_type=update_type, confidence=0.85)

    def get_profile(self, user_id: str) -> Optional[StudentProfile]:
        profile = self.profiles.get(user_id)
        if profile:
            self._ensure_basic_info(profile)
            return profile
            
        profile = self.load_profile_from_disk(user_id)
        if profile:
            self._ensure_basic_info(profile)
            self.profiles[user_id] = profile
        return profile
