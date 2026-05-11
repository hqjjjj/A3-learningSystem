import json
import os
from typing import List, Dict, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import networkx as nx
from openai import OpenAI

# ==================== 数据模型 ====================

class UserProfile(BaseModel):
    user_id: str
    mastered: List[str] = []
    weak_points: List[str] = []
    learning_style: str = "text"       # visual / text / hybrid
    cognitive_level: str = "intermediate"
    learning_pace: str = "normal"
    error_patterns: List[str] = []
    preference: Dict[str, Any] = {}

class PlanRequest(BaseModel):
    user_profile: UserProfile
    target_topic: Optional[str] = None
    is_review: bool = False

class PlanResponse(BaseModel):
    learning_path: List[Dict]
    daily_plan: List[Dict]
    resource_recommendations: List[Dict]
    teaching_strategy: Dict[str, Any]
    reasoning: str

# ==================== 知识图谱 ====================

class KnowledgeGraph:
    
    def __init__(self, memory_path: str):
        self.graph = nx.DiGraph()  # 有向图
        self.topics = {}
        self._load_from_memory(memory_path)
    
    def _load_from_memory(self, memory_path: str):
        with open(memory_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for topic in data.get("topics", []):
            topic_id = topic["id"]
            self.topics[topic_id] = topic
            
            # 添加节点，属性存入
            self.graph.add_node(
                topic_id,
                name=topic.get("name", topic_id),
                difficulty=topic.get("difficulty", "medium"),
                content=str(topic.get("content", {})),
                common_mistakes=topic.get("common_mistakes", [])
            )
            
            # 添加边（前置依赖关系）
            for prereq in topic.get("prerequisites", []):
                if prereq in self.topics or prereq in [t["id"] for t in data.get("topics", [])]:
                    self.graph.add_edge(prereq, topic_id, relation="prerequisite")
    
    def get_prerequisites(self, topic_id: str) -> List[str]:
        """获取直接前置依赖"""
        return list(self.graph.predecessors(topic_id))
    
    def get_all_dependencies(self, topic_id: str) -> Set[str]:
        """获取所有前置依赖（递归）"""
        return set(nx.ancestors(self.graph, topic_id))
    
    def get_dependents(self, topic_id: str) -> List[str]:
        """获取依赖此知识点的其他知识点"""
        return list(self.graph.successors(topic_id))
    
    def get_learning_order(self, topic_ids: List[str]) -> List[str]:
        """拓扑排序（基于子图）"""
        subgraph = self.graph.subgraph(topic_ids)
        try:
            return list(nx.topological_sort(subgraph))
        except nx.NetworkXUnfeasible:
            # 存在循环依赖，返回原顺序
            return topic_ids
    
    def get_prerequisite_chain(self, topic_id: str) -> List[str]:
        """获取完整前置链（从基础到目标）"""
        ancestors = nx.ancestors(self.graph, topic_id)
        chain = list(ancestors)
        chain.append(topic_id)
        return self.get_learning_order(chain)
    
    def find_related_topics(self, topic_id: str, max_depth: int = 2) -> List[str]:
        """查找相关知识点（BFS，用于推荐）"""
        related = set()
        current = {topic_id}
        for _ in range(max_depth):
            neighbors = set()
            for node in current:
                neighbors.update(self.graph.predecessors(node))
                neighbors.update(self.graph.successors(node))
            related.update(neighbors)
            current = neighbors
        related.discard(topic_id)
        return list(related)
    
    def get_node_info(self, topic_id: str) -> Dict:
        """获取节点详细信息"""
        if topic_id not in self.graph:
            return {}
        return {
            "id": topic_id,
            **self.graph.nodes[topic_id],
            "prerequisites": self.get_prerequisites(topic_id),
            "dependents": self.get_dependents(topic_id)
        }

# ==================== Planner Agent（带LLM） ====================

class PlannerAgent:
    def __init__(self, memory_path: str, api_key: str = None):
        # 构建知识图谱
        self.kg = KnowledgeGraph(memory_path)
        print(f"[知识图谱] 已加载 {self.kg.graph.number_of_nodes()} 个节点，{self.kg.graph.number_of_edges()} 条依赖边")
        
        # 初始化 LLM
        self.llm = None
        self.llm_enabled = False
        if api_key:
            try:
                self.llm = OpenAI(
                    api_key=api_key,
                    base_url="https://spark-api-open.xf-yun.com/v1",
                )
                self.llm_enabled = True
                print("[LLM] 讯飞星火已就绪")
            except Exception as e:
                print(f"[LLM] 初始化失败: {e}")
        else:
            print("[LLM] 未提供API Key，将使用规则模式")
    
    def _get_llm_plan(self, profile: UserProfile, target: str = None) -> Dict:
        """使用 LLM 进行智能规划"""
        if not self.llm_enabled:
            return None
        
        # 获取知识图谱摘要
        graph_summary = self._get_graph_summary()
        
        # 构建 Prompt
        system_prompt = """你是一位专业的操作系统教学规划专家。你的任务是根据学生的用户画像和知识图谱，进行个性化的学习路径规划。

你拥有一个完整的内存管理分页机制知识图谱，包含了知识点之间的前置依赖关系（边表示"A是B的前置知识"）。

请严格遵守以下规则：
1. 学习路径必须尊重知识图谱中的依赖关系（不能先学B再学A如果A是B的前置）
2. 薄弱点应该优先安排
3. 难度从易到难递进
4. 每天安排2-3个知识点

输出格式要求（严格JSON）：
{
    "learning_path": ["知识点ID1", "知识点ID2", ...],
    "reasoning": "详细的规划理由（说明为什么这样安排，如何考虑了依赖关系和用户画像）",
    "focus_points": ["重点强调的知识点ID"],
    "estimated_days": 数字,
    "difficulty_progression": "难度递进说明"
}"""

        user_prompt = f"""
用户画像：
- 已掌握：{profile.mastered}
- 薄弱点：{profile.weak_points}
- 学习风格：{profile.learning_style}
- 认知水平：{profile.cognitive_level}
- 学习节奏：{profile.learning_pace}
- 错误模式：{profile.error_patterns}
{"- 学习目标：" + target if target else "- 无特定目标（建议完整学习）"}

知识图谱摘要：
{graph_summary}

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
                max_tokens=2048
            )
            
            result_text = response.choices[0].message.content
            # 提取 JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                return json.loads(json_match.group())
            return None
        except Exception as e:
            print(f"[LLM规划失败] {e}")
            return None
        
    def _get_graph_summary(self) -> str:
        """获取知识图谱摘要供 LLM 参考"""
        nodes = []
        for node_id in self.kg.graph.nodes:
            node_data = self.kg.graph.nodes[node_id]
            nodes.append({
                "id": node_id,
                "name": node_data.get("name", node_id),
                "difficulty": node_data.get("difficulty", "medium"),
                "prerequisites": self.kg.get_prerequisites(node_id)
            })
        return json.dumps(nodes, ensure_ascii=False, indent=2)
    
    def _plan_with_rules(self, profile: UserProfile, target: str = None) -> Tuple[List[str], str]:
        """规则规划（备用/增强）"""
        all_topics = set(self.kg.graph.nodes)
        mastered_set = set(profile.mastered)
        weak_set = set(profile.weak_points)
        
        # 确定需要学习的内容
        if target and target in all_topics:
            needed = self.kg.get_all_dependencies(target)
            needed.add(target)
            if not profile.is_review:
                needed = needed - mastered_set
        else:
            needed = all_topics - mastered_set
        
        if not needed:
            return [], "所有知识点均已掌握"
        
        # 拓扑排序
        needed_list = list(needed)
        sorted_topics = self.kg.get_learning_order(needed_list)
        
        # 薄弱点优先
        weak_first = [t for t in sorted_topics if t in weak_set]
        others = [t for t in sorted_topics if t not in weak_set]
        final_order = weak_first + others
        
        reasoning = f"基于知识图谱拓扑排序，共{len(final_order)}个知识点。薄弱点({len(weak_first)}个)已优先安排。"
        
        return final_order, reasoning
    
    def plan(self, profile: UserProfile, target_topic: str = None, is_review: bool = False) -> PlanResponse:
        """主规划方法"""
        profile.is_review = is_review
        
        # 1. 尝试 LLM 规划
        llm_result = self._get_llm_plan(profile, target_topic)
        
        if llm_result and "learning_path" in llm_result:
            learning_path_ids = llm_result["learning_path"]
            reasoning = llm_result.get("reasoning", "基于LLM智能规划")
            focus_points = llm_result.get("focus_points", profile.weak_points)
        else:
            # 回退到规则规划
            learning_path_ids, reasoning = self._plan_with_rules(profile, target_topic)
            focus_points = profile.weak_points
        
        # 2. 构建路径详情（加入知识图谱信息）
        path_details = []
        for tid in learning_path_ids:
            node_info = self.kg.get_node_info(tid)
            path_details.append({
                "id": tid,
                "name": node_info.get("name", tid),
                "difficulty": node_info.get("difficulty", "medium"),
                "prerequisites": node_info.get("prerequisites", [])
            })
        
        # 3. 生成每日计划
        daily_plan = self._generate_daily_plan(learning_path_ids, profile)
        
        # 4. 资源推荐（基于知识图谱的相关性）
        resources = self._recommend_resources(learning_path_ids, profile, focus_points)
        
        # 5. 教学策略
        teaching_strategy = self._generate_teaching_strategy(profile)
        
        return PlanResponse(
            learning_path=path_details,
            daily_plan=daily_plan,
            resource_recommendations=resources,
            teaching_strategy=teaching_strategy,
            reasoning=reasoning
        )
    
    def _generate_daily_plan(self, path: List[str], profile: UserProfile) -> List[Dict]:
        """生成每日计划"""
        if not path:
            return []
        
        pace_minutes = {"slow": 60, "normal": 90, "fast": 120}
        daily_capacity = pace_minutes.get(profile.learning_pace, 90)
        
        difficulty_time = {"easy": 20, "medium": 35, "hard": 50}
        
        daily_plans = []
        current_day = 1
        current_date = datetime.now()
        current_topics = []
        current_total = 0
        
        for tid in path:
            node = self.kg.graph.nodes.get(tid, {})
            difficulty = node.get("difficulty", "medium")
            minutes = difficulty_time.get(difficulty, 35)
            
            if tid in profile.weak_points:
                minutes = int(minutes * 1.3)
            if profile.learning_pace == "fast":
                minutes = int(minutes * 0.8)
            elif profile.learning_pace == "slow":
                minutes = int(minutes * 1.2)
            
            if current_total + minutes > daily_capacity and current_topics:
                daily_plans.append({
                    "day": current_day,
                    "date": current_date.strftime("%Y-%m-%d"),
                    "topics": current_topics,
                    "topics_name": [self.kg.graph.nodes.get(t, {}).get("name", t) for t in current_topics],
                    "estimated_minutes": current_total
                })
                current_day += 1
                current_date += timedelta(days=1)
                current_topics = []
                current_total = 0
            
            current_topics.append(tid)
            current_total += minutes
        
        if current_topics:
            daily_plans.append({
                "day": current_day,
                "date": current_date.strftime("%Y-%m-%d"),
                "topics": current_topics,
                "topics_name": [self.kg.graph.nodes.get(t, {}).get("name", t) for t in current_topics],
                "estimated_minutes": current_total
            })
        
        return daily_plans
    
    def _recommend_resources(self, path: List[str], profile: UserProfile, focus_points: List[str]) -> List[Dict]:
        """资源推荐（基于知识图谱关系）"""
        recommendations = []
        
        for tid in path[:8]:
            node = self.kg.graph.nodes.get(tid, {})
            topic_name = node.get("name", tid)
            
            # 查找相关知识点（用于扩展推荐）
            related = self.kg.find_related_topics(tid, max_depth=1)
            
            resources = []
            
            # 文本讲解
            resources.append({
                "type": "text",
                "title": f"{topic_name} - 核心讲解",
                "description": node.get("content", "")[:200] if node.get("content") else f"{topic_name}的核心概念讲解"
            })
            
            # 练习（如果有关联的练习题）
            resources.append({
                "type": "exercise",
                "title": f"{topic_name} - 随堂练习",
                "description": f"检验对{topic_name}的理解"
            })
            
            # 如果有关联知识点，推荐复习
            if related and tid in profile.weak_points:
                related_names = [self.kg.graph.nodes.get(r, {}).get("name", r) for r in related[:2]]
                resources.append({
                    "type": "review",
                    "title": f"关联知识复习",
                    "description": f"建议先复习：{', '.join(related_names)}"
                })
            
            # 如果是重点，添加强调
            if tid in focus_points:
                resources.append({
                    "type": "warning",
                    "title": "⭐ 重点掌握",
                    "description": f"{topic_name}是本次学习的核心，请多加练习"
                })
            
            recommendations.append({
                "topic_id": tid,
                "topic_name": topic_name,
                "resources": resources
            })
        
        return recommendations
    
    def _generate_teaching_strategy(self, profile: UserProfile) -> Dict[str, Any]:
        """生成教学策略"""
        style_map = {
            "visual": {"format": "图表+动画", "resource_priority": ["diagram", "video"]},
            "text": {"format": "文字讲解", "resource_priority": ["text", "exercise"]},
            "hybrid": {"format": "图文结合", "resource_priority": ["text", "diagram", "exercise"]}
        }
        
        pace_map = {
            "slow": "细致讲解，多停顿检查",
            "normal": "正常节奏",
            "fast": "快速推进，重点突出"
        }
        
        depth_map = {
            "beginner": "基础概念为主，多举例",
            "intermediate": "原理分析，适当深入",
            "advanced": "底层机制，优化分析"
        }
        
        return {
            "learning_style_strategy": style_map.get(profile.learning_style, style_map["hybrid"]),
            "pace_strategy": pace_map.get(profile.learning_pace, "正常节奏"),
            "depth_strategy": depth_map.get(profile.cognitive_level, "原理分析"),
            "weak_points_emphasis": profile.weak_points,
            "error_prevention": profile.error_patterns
        }
    

# ==================== FastAPI 应用 ====================

app = FastAPI(title="Planner Agent with Knowledge Graph & LLM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = None

@app.on_event("startup")
async def startup():
    global agent
    current_dir = os.path.dirname(os.path.abspath(__file__))
    memory_path = os.path.join(current_dir, "memory.json")
    api_key = os.environ.get("XF_API_KEY")
    agent = PlannerAgent(memory_path, api_key)
    print("[Planner Agent] 启动完成")

@app.get("/")
async def root():
    return {
        "service": "Planner Agent",
        "features": ["Knowledge Graph", "LLM Planning", "Recommendation"],
        "llm_enabled": agent.llm_enabled if agent else False,
        "nodes_count": agent.kg.graph.number_of_nodes() if agent else 0
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "nodes": agent.kg.graph.number_of_nodes(), "edges": agent.kg.graph.number_of_edges()}

@app.get("/graph")
async def get_graph():
    """获取知识图谱结构"""
    nodes = []
    for node_id in agent.kg.graph.nodes:
        nodes.append(agent.kg.get_node_info(node_id))
    edges = [{"source": u, "target": v} for u, v in agent.kg.graph.edges]
    return {"nodes": nodes, "edges": edges}

@app.post("/plan", response_model=PlanResponse)
async def plan(request: PlanRequest):
    result = agent.plan(request.user_profile, request.target_topic, request.is_review)
    return result

@app.get("/prerequisites/{topic_id}")
async def get_prerequisites(topic_id: str):
    """获取某个知识点的前置依赖链"""
    chain = agent.kg.get_prerequisite_chain(topic_id)
    return {"topic": topic_id, "prerequisite_chain": chain}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)