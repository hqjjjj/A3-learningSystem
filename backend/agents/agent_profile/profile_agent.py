import requests
import json
import hashlib
import hmac
import base64
import datetime
import os
import re
from urllib.parse import urlencode
from typing import Dict, List, Optional
from models import StudentProfile, CognitiveStyle, Preference, Progress, ProfileResponse

os.environ["no_proxy"] = "*"

# ============ 加载课程知识图谱 ============
KNOWLEDGE_GRAPH = {}
try:
    agent_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(agent_dir)))
    memory_path = os.path.join(project_root, "data", "knowledge", "memory.json")
    with open(memory_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        for topic in data.get("topics", []):
            KNOWLEDGE_GRAPH[topic["name"]] = topic
    print(f"✅ 成功加载 {len(KNOWLEDGE_GRAPH)} 个课程知识点")
except Exception as e:
    print(f"⚠️ 加载memory.json失败: {e}")

class ProfileAgent:
    def __init__(self, app_id="nide", api_key="nide", api_secret="nide"):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.host = "spark-api-open.xf-yun.com"
        self.path = "/v1/chat/completions"
        self.request_url = f"https://{self.host}{self.path}"
        self.profiles: Dict[str, StudentProfile] = {}

    def _create_url(self) -> str:
        now = datetime.datetime.now(datetime.timezone.utc)
        date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
        signature_origin = f"host: {self.host}\ndate: {date}\nPOST {self.path} HTTP/1.1"
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature = base64.b64encode(signature_sha).decode('utf-8')
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        q = {"authorization": authorization, "date": date, "host": self.host}
        return f"{self.request_url}?{urlencode(q)}"

    def _call_llm(self, system_prompt: str, user_msg: str) -> dict:
        url = self._create_url()
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "generalv3.5",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
            "top_p": 0.7
        }

        max_retries = 2
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=30,
                    proxies={"http": None, "https": None}
                )
                result = resp.json()

                if result.get("code") == 0:
                    content = result["choices"][0]["message"]["content"].strip()
                    if content.startswith("```"):
                        lines = content.split('\n')
                        content = '\n'.join(lines[1:]) if len(lines) > 1 else content
                        if content.endswith("```"):
                            content = content[:-3]
                    content = content.strip()
                    # 修复可能的JSON格式问题
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

        # 构建知识点选择列表
        topics_list = []
        for tname, tdata in KNOWLEDGE_GRAPH.items():
            topics_list.append(f"'{tname}' (难度: {tdata['difficulty']})")
        topics_str = "\n".join(topics_list)

        # 大模型Prompt
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

        # 初始化或获取旧画像
        if not old_profile:
            profile = StudentProfile(user_id=user_id, created_at=datetime.datetime.now())
            # 初始化所有知识点掌握度为 0.0
            for topic_name in KNOWLEDGE_GRAPH:
                profile.knowledge_level[topic_name] = 0.0
            update_type = "init"
        else:
            profile = old_profile
            update_type = "update"

        # === 基础信息更新 ===
        if extraction.get("major"):
            profile.major = extraction["major"]
        if extraction.get("grade"):
            profile.grade = extraction["grade"]
        if extraction.get("course"):
            profile.course = extraction["course"]

        # === 认知风格更新 ===
        if "cognitive_style" in extraction:
            cs = extraction["cognitive_style"]
            total = cs.get("visual", 0) + cs.get("textual", 0) + cs.get("auditory", 0)
            if total > 0:
                profile.cognitive_style = CognitiveStyle(
                    visual=round(cs.get("visual", 0) / total, 2),
                    textual=round(cs.get("textual", 0) / total, 2),
                    auditory=round(cs.get("auditory", 0) / total, 2)
                )
        # === 认知风格转 learning_style (text / diagram) ===
        if profile.cognitive_style.visual >= 0.5:
            profile.learning_style = "diagram"
        else:
            profile.learning_style = "text"

        # === 学习节奏更新 ===
        if extraction.get("learning_pace"):
            profile.learning_pace = extraction["learning_pace"]

        if "resource_type" in extraction and isinstance(extraction["resource_type"], list):
            merged = list(set(profile.resource_type + extraction["resource_type"]))
            profile.resource_type = merged
        if "difficulty" in extraction:
            profile.difficulty = extraction["difficulty"]

        # === 进度更新 ===
        if "progress" in extraction:
            prog = extraction["progress"]
            if prog.get("current_topic"):
                profile.progress.current_topic = prog["current_topic"]

        # ============================================
        # 【纯规则引擎】确定性计算 knowledge_level
        # ============================================
        current_topic = profile.progress.current_topic
        correct_rate = behavior.get("correct_rate", None) if behavior else None

        if current_topic and current_topic in KNOWLEDGE_GRAPH:
            old_score = profile.knowledge_level.get(current_topic, 0.0)

            # 基础分
            base_score = 0.45

            # 行为数据修正
            if correct_rate is not None:
                if correct_rate < 0.4:
                    base_score = 0.25
                elif correct_rate > 0.8:
                    base_score = 0.75

            # 学习节奏修正
            if profile.learning_pace == "slow":
                base_score = min(base_score, 0.4)
            elif profile.learning_pace == "fast":
                base_score = max(base_score, 0.7)

            # 平滑合并
            if old_score == 0.0:
                profile.knowledge_level[current_topic] = base_score
            else:
                profile.knowledge_level[current_topic] = round(old_score * 0.7 + base_score * 0.3, 2)

        # 薄弱点与错误标签
        profile.weak_points = [name for name, score in profile.knowledge_level.items() if 0.0 < score <= 0.3]
        profile.error_tags = [name for name, score in profile.knowledge_level.items() if 0.0 < score <= 0.2]

        profile.updated_at = datetime.datetime.now()
        self.profiles[user_id] = profile
        return ProfileResponse(profile=profile, update_type=update_type, confidence=0.85)

    def get_profile(self, user_id: str) -> Optional[StudentProfile]:
        return self.profiles.get(user_id)


# ============ 测试 ============
if __name__ == "__main__":
    import os

    agent = ProfileAgent(
     app_id=os.environ.get("SPARK_APP_ID", "820d31b7"),
     api_key=os.environ.get("SPARK_API_KEY", ""),
     api_secret=os.environ.get("SPARK_API_SECRET", "")
    )

    print("=" * 50)
    print("测试1：首次对话构建画像")
    print("=" * 50)
    res1 = agent.build_profile("s1", "计算机大三，操作系统分页太难了，我喜欢看视频")
    print(res1.profile.model_dump_json(indent=2))

    print("\n" + "=" * 50)
    print("测试2：增量更新画像")
    print("=" * 50)
    res2 = agent.build_profile("s1", "缺页中断还是不懂，做题正确率好低", behavior={"correct_rate": 0.3})
    print(res2.profile.model_dump_json(indent=2))