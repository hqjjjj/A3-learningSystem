# backend/agents/agent_profile/profile_agent.py
import requests
import json
import datetime
import os
import re
from typing import Dict, List, Optional
from models import StudentProfile, CognitiveStyle, Progress, ProfileResponse

os.environ["no_proxy"] = "*"

# ============ 加载课程知识图谱 ============
KNOWLEDGE_GRAPH = {}
try:
    agent_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(agent_dir)))
    
    # 👇 这里改掉！原来读的是 memory.json，现在改读专门的操作系统章节 memory 文件夹下的 5memory.json
    memory_path = os.path.join(project_root, "data", "knowledge", "5memory.json")
    
    with open(memory_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        for topic in data.get("topics", []):
            KNOWLEDGE_GRAPH[topic["name"]] = topic
    print(f"✅ 成功加载 {len(KNOWLEDGE_GRAPH)} 个课程知识点 (从 5memory.json)")
except Exception as e:
    print(f"⚠️ 加载5memory.json失败: {e}")


class ProfileAgent:
    """学习画像构建智能体"""

    def __init__(self, api_key="OALNHAzMNPceyqfkinMN:iahJPnpBnZEBAxAzsBNq"):
        self.api_key = api_key
        self.base_url = "https://spark-api-open.xf-yun.com/agent/v1/chat/completions"
        self.model = "spark-x"
        self.profiles: Dict[str, StudentProfile] = {}
        
        # 新增：定义画像持久化的根目录
        agent_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(agent_dir)))
        self.data_root = os.path.join(project_root, "data", "profile_outputs")
        # 确保文件夹存在
        os.makedirs(self.data_root, exist_ok=True)

    # ================= 新增：文件持久化方法 =================
    def _save_profile_to_disk(self, profile: StudentProfile):
        """将最新的画像对象同步写入磁盘"""
        file_path = os.path.join(self.data_root, f"profile_{profile.user_id}.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(profile.model_dump_json(indent=2))
        except Exception as e:
            print(f"⚠️ 保存用户 {profile.user_id} 画像失败: {e}")

    def load_profile_from_disk(self, user_id: str) -> Optional[StudentProfile]:
        """从磁盘读取旧的画像数据（用于服务重启后数据恢复）"""
        file_path = os.path.join(self.data_root, f"profile_{user_id}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 利用 Pydantic 的 model_validate 从字典还原对象
                    return StudentProfile.model_validate(data)
            except Exception as e:
                print(f"⚠️ 读取用户 {user_id} 历史画像失败: {e}")
        return None
    # ======================================================

    def _call_llm(self, system_prompt: str, user_msg: str) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            "temperature": 0.1,
            "max_tokens": 1024
        }

        max_retries = 2
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                result = resp.json()

                if result.get("code") == 0:
                    msg = result["choices"][0]["message"]
                    content = msg.get("content", "").strip()
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
                    if content.startswith("```"):
                        lines = content.split('\n')
                        content = '\n'.join(lines[1:]) if len(lines) > 1 else content
                        if content.endswith("```"):
                            content = content[:-3]
                    content = content.strip()
                    content = re.sub(r',\s*}', '}', content)
                    content = re.sub(r',\s*]', ']', content)
                    return json.loads(content)
                else:
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

        raise Exception("API调用失败，已达最大重试次数")

    def build_profile(self, user_id: str, user_input: str,
                      history: List[dict] = None,
                      behavior: dict = None) -> ProfileResponse:
        old_profile = self.profiles.get(user_id)
        
        # 如果没有在内存里，尝试从硬盘读取（防止后端重启后变成新用户）
        if not old_profile:
            old_profile = self.load_profile_from_disk(user_id)
            if old_profile:
                self.profiles[user_id] = old_profile

        topics_list = []
        for tname, tdata in KNOWLEDGE_GRAPH.items():
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
        6. learning_pace: "normal"/"slow"/"fast"，从语气和行为推断
        7. resource_type: 资源类型列表，从["explanation", "mindmap", "exercise", "code_example"]中选择。根据学生偏好和行为动态推断，如喜欢看视频→["explanation", "mindmap"]，做题正确率低→["explanation", "exercise"]
        8. difficulty: "easy"/"medium"/"hard"
        9. learning_goal: 无法推断填null

        ## 输出要求
        必须是合法JSON，无说明文字，无markdown代码块包裹，直接输出纯JSON。"""

        user_message = f"学生输入：{user_input}\n行为数据：{json.dumps(behavior or {}, ensure_ascii=False)}\n旧画像：{old_profile.model_dump() if old_profile else '无'}"

        try:
            extraction = self._call_llm(sys_prompt, user_message)
        except Exception as e:
            print(f"API调用失败: {e}")
            if old_profile:
                return ProfileResponse(profile=old_profile, update_type="update", confidence=0.3)
            empty_profile = StudentProfile(user_id=user_id, created_at=datetime.datetime.now())
            return ProfileResponse(profile=empty_profile, update_type="init", confidence=0.1)

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

        if "progress" in extraction:
            prog = extraction["progress"]
            if prog.get("current_topic"):
                profile.progress.current_topic = prog["current_topic"]

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

        profile.weak_points = [name for name, score in profile.knowledge_level.items() if 0.0 < score <= 0.3]
        profile.error_tags = [name for name, score in profile.knowledge_level.items() if 0.0 < score <= 0.2]

        profile.updated_at = datetime.datetime.now()
        
        # === 核心修改：写入内存并同步写入硬盘 ===
        self.profiles[user_id] = profile
        self._save_profile_to_disk(profile)  # 自动持久化
        
        return ProfileResponse(profile=profile, update_type=update_type, confidence=0.85)

    def get_profile(self, user_id: str) -> Optional[StudentProfile]:
        # 改进了获取逻辑：如果内存没有，帮总控去硬盘找
        profile = self.profiles.get(user_id)
        if not profile:
            profile = self.load_profile_from_disk(user_id)
            if profile:
                self.profiles[user_id] = profile
        return profile