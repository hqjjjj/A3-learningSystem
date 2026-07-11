import json
import os
import networkx as nx
from typing import List, Dict, Set, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from openai import OpenAI

# ==================== 配置 ====================

# 讯飞星火 API Key（从环境变量读取）
# 讯飞星火配置（从控制台获取这三个值）
IFLYTEK_APPID = "574c51e6"           # 一串数字
IFLYTEK_API_SECRET = "Nzg2NTVjMWNlZDYwNmY5ODdmNDk3ZTAw"  # 32位字符串

# 拼接成 OpenAI 兼容接口需要的格式
XFYF_API_KEY = f"{IFLYTEK_APPID}:{IFLYTEK_API_SECRET}"

# ==================== 知识图谱构建 ====================

@dataclass
class KnowledgeNode:
    id: str
    name: str
    difficulty: str
    prerequisites: List[str] = field(default_factory=list)
    x: float = 0
    y: float = 0
class KnowledgeGraph:
    def __init__(self, knowledge_dir: str):
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.name_to_id: Dict[str, str] = {}
        self.id_to_name: Dict[str, str] = {}
        self._load_from_directory(knowledge_dir)
        self._build_graph()
        self._calculate_positions()
    
    def _load_from_directory(self, knowledge_dir: str):
        """从目录加载所有 JSON 文件"""
        if not os.path.exists(knowledge_dir):
            print(f"[路径规划agent][错误] 知识库目录不存在: {knowledge_dir}")
            return
        
        json_files = [f for f in os.listdir(knowledge_dir) if f.endswith('.json')]
        print(f"[知识库] 发现 {len(json_files)} 个文件")
        
        for json_file in json_files:
            file_path = os.path.join(knowledge_dir, json_file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                topics = data.get("topics", data) if isinstance(data, dict) else data
                
                if isinstance(topics, list):
                    for topic in topics:
                        self._add_topic(topic)
                else:
                    print(f"[路径规划agent][警告] {json_file} 格式不正确，跳过")
                    
            except Exception as e:
                print(f"[错误] 读取 {json_file} 失败: {e}")
        
        print(f"[路径规划agent][知识库] 从 {len(json_files)} 个文件加载了 {len(self.nodes)} 个知识点")
    
    def _add_topic(self, topic: dict):
        """添加单个知识点节点"""
        topic_id = topic.get("id")
        if not topic_id:
            return
        
        node = KnowledgeNode(
            id=topic_id,
            name=topic.get("name", topic_id),
            difficulty=topic.get("difficulty", "medium"),
            prerequisites=topic.get("prerequisites", [])
        )
        self.nodes[node.id] = node
        self.name_to_id[node.name] = node.id
        self.id_to_name[node.id] = node.name
    
    def _build_graph(self):
        """构建有向图（依赖关系）"""
        for node in self.nodes.values():
            self.graph.add_node(node.id, name=node.name, difficulty=node.difficulty)
            for prereq in node.prerequisites:
                if prereq in self.nodes:
                    self.graph.add_edge(prereq, node.id)
    
    def _calculate_positions(self):
        """计算节点坐标"""
        try:
            pos = nx.spring_layout(self.graph, k=2, seed=42)
            for node_id, (x, y) in pos.items():
                if node_id in self.nodes:
                    self.nodes[node_id].x = float(x * 500 + 300)
                    self.nodes[node_id].y = float(y * 300 + 200)
        except:
            for i, node_id in enumerate(self.nodes.keys()):
                self.nodes[node_id].x = 100 + i * 150
                self.nodes[node_id].y = 200
    
    def get_prerequisites(self, topic_id: str) -> List[str]:
        return list(self.graph.predecessors(topic_id))
    
    def get_dependents(self, topic_id: str) -> List[str]:
        return list(self.graph.successors(topic_id))
    
    def get_learning_order(self, topic_ids: List[str]) -> List[str]:
        if not topic_ids:
            return []
        subgraph = self.graph.subgraph(topic_ids)
        try:
            return list(nx.topological_sort(subgraph))
        except:
            return topic_ids
    
    def to_json(self) -> Dict:
        nodes = []
        for node_id, node in self.nodes.items():
            nodes.append({
                "id": node_id,
                "name": node.name,
                "difficulty": node.difficulty,
                "x": node.x,
                "y": node.y,
                "prerequisites": node.prerequisites
            })
        
        edges = []
        for node in self.nodes.values():
            for prereq in node.prerequisites:
                if prereq in self.nodes:
                    edges.append({"source": prereq, "target": node.id})
        
        return {"nodes": nodes, "edges": edges}

# ==================== 路径规划器 ====================

class PlannerAgent:
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
       # 改成三个参数
        IFLYTEK_APPID = "574c51e6"           # 一串数字
        IFLYTEK_API_KEY = "mhWmBWSudeBYIxmQSWsm:vVmrsjInCRycULVTeosH"        # 32位字符串
        IFLYTEK_API_SECRET = "Nzg2NTVjMWNlZDYwNmY5ODdmNDk3ZTAw"  # 32位字符串

        self.llm_enabled = True          # ✅ 缩进正确（在 __init__ 里面）
        try:
            from openai import OpenAI
            self.llm = OpenAI(
                api_key=IFLYTEK_API_KEY,
                base_url="https://spark-api-open.xf-yun.com/x2/"
            )
            print("[LLM] 讯飞星火已初始化")
        except Exception as e:
            print(f"[LLM] 初始化失败: {e}")
            self.llm_enabled = False
            self.llm = None
    
    def get_next_topic(self, user_profile: Dict) -> Dict:
        """获取下一个要学习的知识点（所有知识点）"""
        knowledge = user_profile.get("knowledge_level", {})
        weak_points = user_profile.get("weak_points", [])
        completed_topics = user_profile.get("progress", {}).get("completed_topics", [])
        
        need_study = []
        for topic_id, node in self.kg.nodes.items():
            topic_name = node.name
            score = knowledge.get(topic_name, 0.0)
            if score < 0.7 and topic_id not in completed_topics:
                prereqs = self.kg.get_prerequisites(topic_id)
                if all(p in completed_topics for p in prereqs):
                    need_study.append({
                        "id": topic_id,
                        "name": topic_name,
                        "understanding": score,
                        "is_weak": topic_name in weak_points
                    })
        
        if not need_study:
            return {"topic_id": "", "name": "已完成", "understanding": 1.0, "is_review": False}
    
        need_study.sort(key=lambda x: (not x["is_weak"], x["understanding"]))
        next_topic = need_study[0]
    
        return {
            "topic_id": next_topic["id"],
            "name": next_topic["name"],
            "understanding": round(next_topic["understanding"], 2),
            "is_review": next_topic["understanding"] < 0.5 or next_topic["is_weak"]
        }

    def _build_path_response(self, user_profile: Dict, llm_path_names: List[str]) -> Dict:
  
        path_nodes = []
        for name in llm_path_names:
            topic_id = self.kg.name_to_id.get(name)
            if topic_id:
                node = self.kg.nodes.get(topic_id)
                if node:
                    completed_topics = user_profile.get("progress", {}).get("completed_topics", [])
                    status = "completed" if topic_id in completed_topics else "pending"
                    score = user_profile.get("knowledge_level", {}).get(node.name, 0)
                
                    path_nodes.append({
                       "id": topic_id,
                        "name": node.name,
                        "difficulty": node.difficulty,
                        "status": status,
                        "understanding": round(score, 2),
                        "x": node.x,
                        "y": node.y
                    })
    
        if not path_nodes:
            return self._get_learning_path_rule(user_profile)
    
        next_topic = self.get_next_topic(user_profile)
    
        return {
            "learning_path": [n["name"] for n in path_nodes],
            "current_step": user_profile.get("progress", {}).get("current_topic", ""),
            "next_step": next_topic["name"] if next_topic else "",
            "path_nodes": path_nodes,
            "edges": self.kg.to_json()["edges"]
        }

    def get_learning_path(self, user_profile: Dict) -> Dict:
        knowledge = user_profile.get("knowledge_level", {})
        completed_topics = user_profile.get("progress", {}).get("completed_topics", [])
        
        all_topics = list(self.kg.nodes.keys())
        ordered = self.kg.get_learning_order(all_topics)
        
        path_nodes = []
        for topic_id in ordered:
            node = self.kg.nodes[topic_id]
            score = knowledge.get(node.name, 0)
            
            if topic_id in completed_topics:
                status = "completed"
            else:
                status = "pending"
            
            path_nodes.append({
                "id": topic_id,
                "name": node.name,
                "difficulty": node.difficulty,
                "status": status,
                "understanding": round(score, 2),
                "x": node.x,
                "y": node.y
            })
        
        edges = []
        for node in self.kg.nodes.values():
            for prereq in node.prerequisites:
                if prereq in self.kg.nodes:
                    edges.append({"source": prereq, "target": node.id})
        
        return {
            "learning_path": [n["name"] for n in path_nodes if n["status"] != "completed"],
            "current_step": user_profile.get("progress", {}).get("current_topic", ""),
            "next_step": self.get_next_topic(user_profile)["name"],
            "path_nodes": path_nodes,
            "edges": edges
        }
        
    def get_teaching_output(self, user_profile: Dict, next_topic: Dict) -> Dict:
        knowledge = user_profile.get("knowledge_level", {})
        scores = list(knowledge.values())
        avg_score = sum(scores) / len(scores) if scores else 0.5
        
        if avg_score < 0.3:
            cognitive_level = "beginner"
        elif avg_score < 0.7:
            cognitive_level = "intermediate"
        else:
            cognitive_level = "advanced"
        
        cognitive_style = user_profile.get("cognitive_style", {})
        if cognitive_style:
            learning_style = max(cognitive_style, key=cognitive_style.get)
        else:
            learning_style = user_profile.get("learning_style", "hybrid")
        
        resource_type = user_profile.get("resource_type", "text")
        if isinstance(resource_type, str):
            resource_type = [resource_type]
        
        return {
            "learning_style": learning_style,
            "weak_points": user_profile.get("weak_points", []),
            "cognitive_level": {
                "level": cognitive_level,
                "understanding_avg": round(avg_score, 2)
            },
            "error_patterns": user_profile.get("error_tags", user_profile.get("weak_points", [])),
            "preference": {
                "resource_type": resource_type,
                "difficulty": user_profile.get("difficulty", "medium")
            },
            "learning_pace": user_profile.get("learning_pace", "normal"),
            "current_topic": {
                "id": next_topic["topic_id"],
                "name": next_topic["name"],
                "is_review": next_topic["is_review"]
            }
        }
    
    def update_from_error(self, user_profile: Dict, error_topic_name: str) -> Dict:
        """
        做题错误后动态调整学习路径（不修改用户画像）
        只返回更新后的下一个知识点和学习路径
        """
        # 复制一份临时数据，只用于计算路径
        temp_knowledge = user_profile.get("knowledge_level", {}).copy()
        temp_weak = user_profile.get("weak_points", []).copy()
        temp_completed = user_profile.get("progress", {}).get("completed_topics", []).copy()
    
        # 1. 降低该知识点的理解度（用于判断是否需要复习）
        current_score = temp_knowledge.get(error_topic_name, 0.5)
        new_score = max(0, current_score - 0.2)
        temp_knowledge[error_topic_name] = new_score
    
        # 2. 加入薄弱点
        if error_topic_name not in temp_weak:
            temp_weak.append(error_topic_name)
    
        # 3. 从已完成中移除（需要重新学习）
        error_id = self.kg.name_to_id.get(error_topic_name)
        if error_id and error_id in temp_completed:
            temp_completed.remove(error_id)
    
        # 4. 用临时数据重新计算下一个知识点
        temp_profile = user_profile.copy()
        temp_profile["knowledge_level"] = temp_knowledge
        temp_profile["weak_points"] = temp_weak
        temp_profile["progress"] = {
            "current_topic": None,
            "completed_topics": temp_completed
        }
    
    # 返回新的下一个知识点
        return self.get_next_topic(temp_profile)
    
    def plan_with_llm(self, user_profile: Dict) -> Dict:
        if not self.llm_enabled:
            return None
        
        graph_summary = []
        for node in self.kg.nodes.values():
            graph_summary.append({
                "name": node.name,
                "difficulty": node.difficulty,
                "prerequisites": [self.kg.nodes[p].name for p in node.prerequisites if p in self.kg.nodes]
            })
        
        prompt = f"""
你是操作系统教学规划专家。根据用户画像和知识图谱，规划学习路径。

用户画像：
- 已掌握知识点：{user_profile.get('progress', {}).get('completed_topics', [])}
- 薄弱点：{user_profile.get('weak_points', [])}
- 当前学习：{user_profile.get('progress', {}).get('current_topic')}

知识图谱：
{json.dumps(graph_summary, ensure_ascii=False, indent=2)}

请输出 JSON 格式的学习路径（知识点名称列表）：
{{"learning_path": ["知识点1", "知识点2", ...]}}
"""
        
        try:
            response = self.llm.chat.completions.create(
                model="spark-x",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            result_text = response.choices[0].message.content
            print(f"[LLM] 响应: {result_text[:200]}")

            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                return json.loads(json_match.group())
            return None
        except Exception as e:
            print(f"[LLM] 调用失败: {e}")
            return None

# ==================== 工具函数 ====================

def load_user_profile(filepath: str) -> Dict:
    """从文件加载用户画像"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Dict, filepath: str):
    """保存 JSON 文件"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ 已输出: {filepath}")


def run_planner(KNOWLEDGE_DIR: str, user_profile: Dict, output_dir: str = "."):
    """运行规划器主流程"""
    kg = KnowledgeGraph(KNOWLEDGE_DIR)
    planner = PlannerAgent(kg)
    
    # 1. 输出知识图谱
    save_json(kg.to_json(), os.path.join(output_dir, "knowledge_graph.json"))
    
    # 2. 计算下一个知识点
    next_topic = planner.get_next_topic(user_profile)
    
    # 3. 输出给资源生成模块
    teaching_output = planner.get_teaching_output(user_profile, next_topic)
    save_json(teaching_output, os.path.join(output_dir, "teaching_output.json"))
    
    # 4. 输出学习路径
    learning_path = planner.get_learning_path(user_profile)
    save_json(learning_path, os.path.join(output_dir, "learning_path.json"))
    
    return planner, user_profile, next_topic