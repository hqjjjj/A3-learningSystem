import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from openai import OpenAI

# ==================== 数据模型（API 输入输出） ====================

class UserProfile(BaseModel):
    """用户画像"""
    user_id: str
    mastered: List[str] = []           # 已掌握的知识点ID
    weak_points: List[str] = []        # 薄弱点ID
    learning_style: str = "text"       # visual / text / hybrid
    cognitive_level: str = "intermediate"  # beginner / intermediate / advanced
    learning_pace: str = "normal"      # slow / normal / fast
    preference: Dict[str, Any] = {}    # 资源偏好
    error_patterns: List[str] = []     # 常见错误模式

class PlanRequest(BaseModel):
    """规划请求"""
    user_profile: UserProfile
    target_topic: Optional[str] = None  # 目标知识点（可选）
    is_review: bool = False              # 是否为复习模式

class LearningPathResponse(BaseModel):
    """学习路径响应"""
    learning_path: List[str]            # 知识点ID顺序
    path_details: List[Dict]            # 带名称的详细路径
    reasoning: str                      # 规划理由

class DailyPlanItem(BaseModel):
    """每日计划项"""
    day: int
    date: str
    topics: List[str]
    topics_detail: List[Dict]
    estimated_minutes: int

class ResourceItem(BaseModel):
    """资源项"""
    type: str        # video / text / exercise / diagram
    title: str
    description: str
    url: str = ""

class PlanResponse(BaseModel):
    """完整规划响应"""
    learning_path: LearningPathResponse
    daily_plan: List[DailyPlanItem]
    resource_recommendations: List[Dict]
    teaching_strategy: Dict[str, Any]

# ==================== Planner Agent 核心 ====================

class PlannerAgent:
    def __init__(self, memory_path: str = None, api_key: str = None):
        # 获取当前文件所在目录
        if memory_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            memory_path = os.path.join(current_dir, "memory.json")
        
        # 加载知识库
        with open(memory_path, "r", encoding="utf-8") as f:
            self.memory = json.load(f)
        
        self.topics = {topic["id"]: topic for topic in self.memory.get("topics", [])}
        
        # 构建前置依赖图
        self.prerequisite_graph = {}
        for topic_id, topic in self.topics.items():
            self.prerequisite_graph[topic_id] = topic.get("prerequisites", [])
        
        # 初始化讯飞星火 LLM
        if api_key:
            self.llm = OpenAI(
                api_key="9ab992eba3c8116b816509185aa54fae",
                base_url="https://spark-api-open.xf-yun.com/v1",
            )
            self.llm_enabled = True
        else:
            self.llm = None
            self.llm_enabled = False
            print("[警告] 未提供API Key，将使用规则模式（不调用LLM）")
    
    def _get_prerequisites(self, topic_id: str) -> List[str]:
        return self.prerequisite_graph.get(topic_id, [])
    
    def _get_all_dependencies(self, topic_id: str, visited: set = None) -> set:
        """获取某个知识点的所有前置依赖"""
        if visited is None:
            visited = set()
        for prereq in self._get_prerequisites(topic_id):
            if prereq not in visited:
                visited.add(prereq)
                self._get_all_dependencies(prereq, visited)
        return visited
    
    def _topological_sort(self, topic_ids: List[str]) -> List[str]:
        """拓扑排序（按依赖关系）"""
        if not topic_ids:
            return []
        
        # 构建图
        graph = {tid: [] for tid in topic_ids}
        in_degree = {tid: 0 for tid in topic_ids}
        
        for tid in topic_ids:
            for prereq in self._get_prerequisites(tid):
                if prereq in topic_ids:
                    graph.setdefault(prereq, []).append(tid)
                    in_degree[tid] += 1
        
        # Kahn算法
        queue = [tid for tid in topic_ids if in_degree[tid] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 如果有未处理的，追加
        for tid in topic_ids:
            if tid not in result:
                result.append(tid)
        
        return result
    
    def _get_difficulty_weight(self, difficulty: str) -> float:
        """获取难度权重"""
        weights = {"easy": 1.0, "medium": 1.5, "hard": 2.0}
        return weights.get(difficulty, 1.0)
    
    def _plan_with_llm(self, profile: UserProfile, needed_topics: List[str], target: str = None) -> Dict:
        """使用 LLM 进行智能规划"""
        if not self.llm_enabled:
            return None
        
        # 构建提示词
        topics_info = []
        for tid in needed_topics:
            topic = self.topics.get(tid, {})
            topics_info.append({
                "id": tid,
                "name": topic.get("name", tid),
                "difficulty": topic.get("difficulty", "medium"),
                "prerequisites": topic.get("prerequisites", [])
            })
        
        system_prompt = """你是一位专业的操作系统课程教学规划专家。
你的任务是根据学生的用户画像和课程知识结构，规划个性化的学习路径。

输出格式要求（严格JSON）：
{
    "learning_path": ["知识点ID1", "知识点ID2", ...],
    "reasoning": "规划理由说明",
    "strategy": {
        "explanation_depth": "讲解深度（beginner/intermediate/advanced）",
        "focus_points": ["重点知识点ID"],
        "suggested_pace": "建议节奏（slow/normal/fast）"
    }
}

注意：
1. 学习路径必须遵循前置依赖关系
2. 薄弱点应该优先安排
3. 考虑学生的认知水平和学习节奏"""

        user_prompt = f"""
学生画像：
- 已掌握知识点：{profile.mastered}
- 薄弱点：{profile.weak_points}
- 学习风格：{profile.learning_style}
- 认知水平：{profile.cognitive_level}
- 学习节奏：{profile.learning_pace}
- 常见错误模式：{profile.error_patterns}
{"- 目标知识点：" + target if target else "- 无特定目标，建议完整学习路径"}

课程知识结构（需要学习的内容）：
{json.dumps(topics_info, ensure_ascii=False, indent=2)}

请规划学习路径。
"""
                
        try:
            response = self.llm.chat.completions.create(
                model="spark-lite",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content
            # 提取JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                return json.loads(json_match.group())
            return None
        except Exception as e:
            print(f"[LLM规划失败] {e}")
            return None
    
    def _plan_with_rules(self, profile: UserProfile, needed_topics: List[str]) -> List[str]:
        """使用规则进行规划（备用方案）"""
        mastered_set = set(profile.mastered)
        weak_set = set(profile.weak_points)
        
        # 先拓扑排序
        sorted_topics = self._topological_sort(needed_topics)
        
        # 根据薄弱点调整优先级
        weak_first = [tid for tid in sorted_topics if tid in weak_set]
        others = [tid for tid in sorted_topics if tid not in weak_set]
        
        return weak_first + others
    
    def plan(self, profile: UserProfile, target_topic: str = None, is_review: bool = False) -> PlanResponse:
        """核心规划方法"""
        mastered_set = set(profile.mastered)
        
        # 1. 确定需要学习的知识点
        if target_topic and target_topic in self.topics:
            # 有目标：包含所有前置依赖
            dependencies = self._get_all_dependencies(target_topic)
            needed = dependencies.union({target_topic})
            # 过滤已掌握的（复习模式除外）
            if not is_review:
                needed = needed - mastered_set
            needed = list(needed)
        else:
            # 无目标：学习所有未掌握的
            all_topics = set(self.topics.keys())
            if is_review:
                needed = list(all_topics)
            else:
                needed = list(all_topics - mastered_set)
        
        if not needed:
            # 没有需要学习的内容
            empty_response = LearningPathResponse(
                learning_path=[],
                path_details=[],
                reasoning="所有知识点均已掌握，无需学习"
            )
            return PlanResponse(
                learning_path=empty_response,
                daily_plan=[],
                resource_recommendations=[],
                teaching_strategy={}
            )
        
        # 2. 尝试用LLM规划
        llm_result = self._plan_with_llm(profile, needed, target_topic)
        
        if llm_result and "learning_path" in llm_result:
            learning_path_ids = llm_result["learning_path"]
            reasoning = llm_result.get("reasoning", "基于LLM智能规划")
            strategy = llm_result.get("strategy", {})
        else:
            # 规则规划
            learning_path_ids = self._plan_with_rules(profile, needed)
            reasoning = "基于规则引擎规划（前置依赖优先，薄弱点优先）"
            strategy = {
                "explanation_depth": profile.cognitive_level,
                "focus_points": profile.weak_points,
                "suggested_pace": profile.learning_pace
            }
        
        # 3. 生成详细路径（带名称）
        path_details = []
        for tid in learning_path_ids:
            topic = self.topics.get(tid, {})
            path_details.append({
                "id": tid,
                "name": topic.get("name", tid),
                "difficulty": topic.get("difficulty", "medium")
            })
        
        learning_path_resp = LearningPathResponse(
            learning_path=learning_path_ids,
            path_details=path_details,
            reasoning=reasoning
        )
        
        # 4. 生成每日计划
        daily_plan = self._generate_daily_plan(learning_path_ids, profile)
        
        # 5. 生成资源推荐
        resources = self._recommend_resources(learning_path_ids, profile)
        
        # 6. 生成教学策略
        teaching_strategy = self._generate_teaching_strategy(profile, strategy)
        
        return PlanResponse(
            learning_path=learning_path_resp,
            daily_plan=daily_plan,
            resource_recommendations=resources,
            teaching_strategy=teaching_strategy
        )
    
    def _generate_daily_plan(self, learning_path: List[str], profile: UserProfile) -> List[DailyPlanItem]:
        """生成每日学习计划"""
        if not learning_path:
            return []
        
        # 根据学习节奏确定每天学习时长（分钟）
        pace_minutes = {"slow": 60, "normal": 90, "fast": 120}
        daily_capacity = pace_minutes.get(profile.learning_pace, 90)
        
        # 估算每个知识点所需时间
        topic_times = {}
        for tid in learning_path:
            topic = self.topics.get(tid, {})
            difficulty = topic.get("difficulty", "medium")
            base_time = {"easy": 20, "medium": 35, "hard": 50}
            minutes = base_time.get(difficulty, 35)
            
            # 薄弱点额外加时
            if tid in profile.weak_points:
                minutes = int(minutes * 1.3)
            
            # 快节奏减时
            if profile.learning_pace == "fast":
                minutes = int(minutes * 0.8)
            elif profile.learning_pace == "slow":
                minutes = int(minutes * 1.2)
            
            topic_times[tid] = minutes
        
        # 按天拆分
        daily_plans = []
        current_day = 1
        current_date = datetime.now()
        current_topics = []
        current_total = 0
        
        for tid in learning_path:
            time_needed = topic_times[tid]
            
            if current_total + time_needed > daily_capacity and current_topics:
                # 超出容量，保存当天计划
                daily_plans.append(DailyPlanItem(
                    day=current_day,
                    date=current_date.strftime("%Y-%m-%d"),
                    topics=current_topics,
                    topics_detail=[
                        {"id": t, "name": self.topics.get(t, {}).get("name", t)}
                        for t in current_topics
                    ],
                    estimated_minutes=current_total
                ))
                current_day += 1
                current_date += timedelta(days=1)
                current_topics = []
                current_total = 0
            
            current_topics.append(tid)
            current_total += time_needed
        
        # 最后一天
        if current_topics:
            daily_plans.append(DailyPlanItem(
                day=current_day,
                date=current_date.strftime("%Y-%m-%d"),
                topics=current_topics,
                topics_detail=[
                    {"id": t, "name": self.topics.get(t, {}).get("name", t)}
                    for t in current_topics
                ],
                estimated_minutes=current_total
            ))
        
        return daily_plans

    def _recommend_resources(self, learning_path: List[str], profile: UserProfile) -> List[Dict]:
        """推荐学习资源"""
        recommendations = []
        
        # 资源类型权重
        type_weights = {
            "text": 0.3,
            "diagram": 0.2,
            "exercise": 0.3,
            "video": 0.2
        }
        
        # 根据用户偏好调整
        pref = profile.preference
        if pref.get("prefer_video"):
            type_weights["video"] += 0.2
            type_weights["text"] -= 0.1
        if pref.get("prefer_exercise"):
            type_weights["exercise"] += 0.2
        if profile.learning_style == "visual":
            type_weights["diagram"] += 0.2
            type_weights["text"] -= 0.1
        
        for tid in learning_path[:10]:  # 限制数量
            topic = self.topics.get(tid, {})
            resources = []
            
            # 文本资源
            if type_weights.get("text", 0) > 0.1:
                resources.append(ResourceItem(
                    type="text",
                    title=f"{topic.get('name', tid)} - 文字讲解",
                    description=topic.get("content", {}).get("explanation", "核心知识点讲解")
                ))
            
            # 图解资源
            if type_weights.get("diagram", 0) > 0.1:
                resources.append(ResourceItem(
                    type="diagram",
                    title=f"{topic.get('name', tid)} - 原理图解",
                    description="可视化展示核心概念"
                ))
            
            # 练习题
            if type_weights.get("exercise", 0) > 0.1:
                questions = topic.get("questions", [])
                if questions:
                    resources.append(ResourceItem(
                        type="exercise",
                        title=f"{topic.get('name', tid)} - 随堂练习",
                        description=questions[0].get("question", "测试你的理解")
                    ))
            
            # 常见错误提醒
            if topic.get("common_mistakes") and tid in profile.weak_points:
                resources.append(ResourceItem(
                    type="text",
                    title=f"{topic.get('name', tid)} - 常见错误",
                    description=f"注意避免：{', '.join(topic.get('common_mistakes', []))}"
                ))
            
            recommendations.append({
                "topic_id": tid,
                "topic_name": topic.get("name", tid),
                "resources": [res.dict() for res in resources]
            })
        
        return recommendations
    
    def _generate_teaching_strategy(self, profile: UserProfile, llm_strategy: Dict = None) -> Dict[str, Any]:
        """生成教学策略"""
        depth_map = {
            "beginner": "详细讲解基础概念，多举例说明",
            "intermediate": "讲清核心原理，适当对比分析",
            "advanced": "深入底层原理，扩展高级知识"
        }
        
        format_map = {
            "visual": "多用图表和动画演示",
            "text": "以文字讲解为主",
            "hybrid": "图文结合，根据内容选择"
        }
        
        pace_map = {
            "slow": "每分钟拆解，多停顿检查理解",
            "normal": "知识点为单位，连贯讲解",
            "fast": "整体概述，重点突出"
        }
        
        strategy = {
            "explanation_depth": depth_map.get(profile.cognitive_level, depth_map["intermediate"]),
            "output_format": format_map.get(profile.learning_style, format_map["hybrid"]),
            "learning_pace_strategy": pace_map.get(profile.learning_pace, pace_map["normal"]),
            "focus_topics": profile.weak_points,
            "error_warnings": profile.error_patterns,
            "resource_preference": profile.preference
        }
        
        if llm_strategy:
            strategy.update(llm_strategy)
        
        return strategy


# ==================== FastAPI 接口 ====================

app = FastAPI(title="Planner Agent", description="个性化学习路径规划服务")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局 Agent 实例
agent = None

@app.on_event("startup")
async def startup_event():
    global agent
    api_key = os.environ.get("XF_API_KEY")  # 从环境变量读取
    agent = PlannerAgent(api_key=api_key)
    print("[Planner Agent] 初始化完成")

@app.get("/")
async def root():
    return {"service": "Planner Agent", "status": "running", "version": "1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "topics_count": len(agent.topics) if agent else 0}

@app.get("/topics")
async def get_topics():
    """获取所有知识点"""
    return {"topics": list(agent.topics.values()) if agent else []}

@app.post("/plan", response_model=PlanResponse)
async def create_plan(request: PlanRequest):
    """规划学习路径"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent未初始化")
    
    try:
        result = agent.plan(
            profile=request.user_profile,
            target_topic=request.target_topic,
            is_review=request.is_review
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/plan/simple")
async def simple_plan(user_profile: UserProfile, target_topic: str = None):
    """简化版规划（快速测试）"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent未初始化")
    
    result = agent.plan(profile=user_profile, target_topic=target_topic)
    
    return {
        "learning_path": result.learning_path.learning_path,
        "daily_plan_summary": [
            {"day": d.day, "topics": d.topics, "minutes": d.estimated_minutes}
            for d in result.daily_plan
        ],
        "reasoning": result.learning_path.reasoning
    }


# ==================== 启动 ====================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)