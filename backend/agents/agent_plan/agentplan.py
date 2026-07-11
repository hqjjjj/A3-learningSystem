import json
import os
import networkx as nx
from typing import List, Dict, Set, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from openai import OpenAI
import time
import threading
import hashlib

# ==================== 配置 ====================

# 获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../.."))

# 监听目录（别人放用户画像的地方）
WATCH_DIR = os.path.join(project_root, "data", "profile_outputs")

# 输出目录（你的输出）
OUTPUT_DIR = os.path.join(project_root, "data", "planner")

# 知识库目录
KNOWLEDGE_DIR = os.path.join(project_root, "data", "knowledge")

# 讯飞星火 API 配置
IFLYTEK_APPID = "574c51e6"
IFLYTEK_API_KEY = "mhWmBWSudeBYIxmQSWsm:vVmrsjInCRycULVTeosH"
IFLYTEK_API_SECRET = "Nzg2NTVjMWNlZDYwNmY5ODdmNDk3ZTAw"

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
        
        self.llm_enabled = True
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
        """构建路径响应（从 LLM 生成的名字列表）"""
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
            "learning_path": [n["name"] for n in path_nodes if n["status"] != "completed"],
            "current_step": user_profile.get("progress", {}).get("current_topic", ""),
            "next_step": next_topic["name"] if next_topic else "",
            "path_nodes": path_nodes,
            "edges": self.kg.to_json()["edges"],
            "timestamp": datetime.now().isoformat()
        }

    def _get_learning_path_rule(self, user_profile: Dict) -> Dict:
        """规则兜底：基于拓扑排序生成学习路径"""
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
            "edges": edges,
            "timestamp": datetime.now().isoformat()
        }

    def get_learning_path(self, user_profile: Dict) -> Dict:
        """
        获取个性化学习路径
        优先使用 LLM 生成，失败则用规则兜底
        """
        # 策略1: LLM 个性化路径
        if self.llm_enabled:
            llm_result = self.plan_with_llm(user_profile)
            if llm_result and "learning_path" in llm_result:
                print("[路径规划] ✅ 使用 LLM 生成个性化路径")
                return self._build_path_response(user_profile, llm_result["learning_path"])
        
        # 策略2: 规则兜底（拓扑排序）
        print("[路径规划] ⚠️ 使用规则兜底生成路径")
        return self._get_learning_path_rule(user_profile)
        
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
        temp_knowledge = user_profile.get("knowledge_level", {}).copy()
        temp_weak = user_profile.get("weak_points", []).copy()
        temp_completed = user_profile.get("progress", {}).get("completed_topics", []).copy()
    
        current_score = temp_knowledge.get(error_topic_name, 0.5)
        new_score = max(0, current_score - 0.2)
        temp_knowledge[error_topic_name] = new_score
    
        if error_topic_name not in temp_weak:
            temp_weak.append(error_topic_name)
    
        error_id = self.kg.name_to_id.get(error_topic_name)
        if error_id and error_id in temp_completed:
            temp_completed.remove(error_id)
    
        temp_profile = user_profile.copy()
        temp_profile["knowledge_level"] = temp_knowledge
        temp_profile["weak_points"] = temp_weak
        temp_profile["progress"] = {
            "current_topic": None,
            "completed_topics": temp_completed
        }
    
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
        
        completed = user_profile.get('progress', {}).get('completed_topics', [])
        weak = user_profile.get('weak_points', [])
        knowledge = user_profile.get('knowledge_level', {})
        
        weak_names = [name for name, score in knowledge.items() if score < 0.6]
        weak_names.extend(weak)
        weak_names = list(set(weak_names))
        
        prompt = f"""
你是操作系统教学规划专家。根据用户画像和知识图谱，规划个性化的学习路径。

【用户画像】
- 已掌握知识点：{completed}
- 薄弱知识点：{weak_names}
- 当前学习进度：{user_profile.get('progress', {}).get('current_topic', '未开始')}

【知识图谱】（包含依赖关系）
{json.dumps(graph_summary, ensure_ascii=False, indent=2)}

【任务要求】
1. 优先安排用户的薄弱知识点
2. 必须遵循知识点之间的依赖关系（先学前置知识）
3. 学习路径长度适中，建议5-10个知识点
4. 只输出JSON格式，不要其他文字

请输出学习路径（知识点名称列表）：
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

# ==================== 文件监控器 ====================

class UserProfileMonitor:
    """监控用户画像文件变化，自动重新生成学习路径"""
    
    def __init__(self, planner: PlannerAgent, watch_dir: str, output_dir: str, check_interval: float = 1.0):
        self.planner = planner
        self.watch_dir = watch_dir
        self.output_dir = output_dir
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        self.callbacks = []
        self.file_hashes = {}
        
        # 确保目录存在
        os.makedirs(watch_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
    
    def _get_file_hash(self, filepath: str) -> str:
        """计算文件内容的 MD5 哈希"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def _process_user_profile(self, filepath: str):
        """处理用户画像文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                user_profile = json.load(f)
            
            filename = os.path.basename(filepath)
            print(f"\n{'='*60}")
            print(f"[监控] 📁 检测到用户画像变化: {filename}")
            print(f"[监控] 🕐 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 获取用户ID
            user_id = user_profile.get('user_id', os.path.splitext(filename)[0])
            
            # 重新生成学习路径（使用LLM）
            learning_path = self.planner.get_learning_path(user_profile)
            
            # 保存到输出目录（按用户ID分类）
            user_output_dir = os.path.join(self.output_dir, user_id)
            os.makedirs(user_output_dir, exist_ok=True)
            
            # 保存最新版本
            output_path = os.path.join(user_output_dir, "learning_path.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(learning_path, f, indent=2, ensure_ascii=False)
            
            print(f"[监控] ✅ 学习路径已更新: {output_path}")
            
            # 保存历史版本
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            history_path = os.path.join(user_output_dir, f"learning_path_{timestamp}.json")
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(learning_path, f, indent=2, ensure_ascii=False)
            
            print(f"[监控] 📚 历史版本已保存: {history_path}")
            
            # 保存教学输出
            next_topic = self.planner.get_next_topic(user_profile)
            teaching_output = self.planner.get_teaching_output(user_profile, next_topic)
            teaching_path = os.path.join(user_output_dir, "teaching_output.json")
            with open(teaching_path, 'w', encoding='utf-8') as f:
                json.dump(teaching_output, f, indent=2, ensure_ascii=False)
            
            print(f"[监控] 📊 教学输出已保存: {teaching_path}")
            print(f"[监控] 📊 路径长度: {len(learning_path.get('learning_path', []))} 个知识点")
            print(f"[监控] ➡️  下一步: {learning_path.get('next_step', '无')}")
            print(f"{'='*60}\n")
            
            # 更新哈希
            self.file_hashes[filepath] = self._get_file_hash(filepath)
            
            # 触发回调
            for callback in self.callbacks:
                try:
                    callback(user_profile, learning_path, user_id)
                except Exception as e:
                    print(f"[监控] 回调执行失败: {e}")
            
            return learning_path
            
        except Exception as e:
            print(f"[监控] ❌ 处理 {filepath} 失败: {e}")
            return None
    
    def _check_and_process(self):
        """检查目录中的新文件或更新文件"""
        if not os.path.exists(self.watch_dir):
            return
        
        json_files = [f for f in os.listdir(self.watch_dir) if f.endswith('.json')]
        
        for filename in json_files:
            filepath = os.path.join(self.watch_dir, filename)
            current_hash = self._get_file_hash(filepath)
            
            # 如果是新文件或文件内容已变化
            if filepath not in self.file_hashes or self.file_hashes.get(filepath) != current_hash:
                self._process_user_profile(filepath)
                time.sleep(0.1)
    
    def _monitor_loop(self):
        """监控循环"""
        print(f"[监控] 🔍 开始监控目录: {self.watch_dir}")
        print(f"[监控] ⏱️  检查间隔: {self.check_interval} 秒")
        print(f"[监控] 📁 输出目录: {self.output_dir}")
        print(f"[监控] 按 Ctrl+C 停止监控\n")
        
        # 首次立即执行
        self._check_and_process()
        
        while self.running:
            time.sleep(self.check_interval)
            self._check_and_process()
    
    def start(self):
        """启动监控"""
        if self.running:
            print("[监控] 监控已在运行中")
            return
        
        if not os.path.exists(self.watch_dir):
            print(f"[监控] ⚠️  监控目录不存在，将创建: {self.watch_dir}")
            os.makedirs(self.watch_dir, exist_ok=True)
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止监控"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("[监控] 监控已停止")
    
    def add_callback(self, callback):
        """添加回调函数，在路径更新时调用"""
        self.callbacks.append(callback)

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

# ==================== 主函数（输入输出完全不变） ====================

def run_planner(KNOWLEDGE_DIR: str, user_profile: Dict, output_dir: str = "."):
    """
    运行规划器主流程（输入输出完全不变）
    
    参数:
        KNOWLEDGE_DIR: 知识库目录
        user_profile: 用户画像字典（直接传字典，不是文件路径）
        output_dir: 输出目录
    
    返回:
        planner: PlannerAgent 实例
        user_profile: 用户画像字典（原样返回）
        next_topic: 下一个知识点
    """
    # 创建必要的目录
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # 初始化知识图谱
    kg = KnowledgeGraph(KNOWLEDGE_DIR)
    
    # 1. 输出知识图谱
    save_json(kg.to_json(), os.path.join(output_dir, "knowledge_graph.json"))
    
    # 初始化规划器
    planner = PlannerAgent(kg)
    
    # 2. 计算下一个知识点
    next_topic = planner.get_next_topic(user_profile)
    
    # 3. 输出给资源生成模块
    teaching_output = planner.get_teaching_output(user_profile, next_topic)
    save_json(teaching_output, os.path.join(output_dir, "teaching_output.json"))
    
    # 4. 输出学习路径（使用LLM规划）
    learning_path = planner.get_learning_path(user_profile)
    save_json(learning_path, os.path.join(output_dir, "learning_path.json"))

       # ============ 新增：输出 {user_id}.json（与监控服务位置和格式完全一致） ============
    user_id = user_profile.get("user_id", "unknown")
    
    # 构建 current_topic
    user_current_topic = user_profile.get("progress", {}).get("current_topic")
    if user_current_topic:
        topic_id = planner.kg.name_to_id.get(user_current_topic)
        understanding = user_profile.get("knowledge_level", {}).get(user_current_topic, 0.0)
        is_review = user_current_topic in user_profile.get("weak_points", [])
        current_topic_output = {
            "id": topic_id or "",
            "name": user_current_topic,
            "understanding": understanding,
            "is_review": is_review
        }
    else:
        current_topic_output = {
            "id": next_topic.get("topic_id", ""),
            "name": next_topic.get("name", ""),
            "understanding": next_topic.get("understanding", 0.0),
            "is_review": next_topic.get("is_review", False)
        }
    
    # 构建 teaching_output（包含 current_topic）
    teaching_output_with_current = teaching_output.copy()
    teaching_output_with_current["current_topic"] = current_topic_output
    
    # ✅ 输出到 output_dir 目录下，文件名 {user_id}.json（与监控服务完全一致）
    user_output_file = os.path.join(output_dir, f"{user_id}.json")
    with open(user_output_file, "w", encoding="utf-8") as f:
        json.dump({
            "user_id": user_id,
            "current_topic": current_topic_output,
            "teaching_output": teaching_output_with_current,
            "learning_path": learning_path,
            "updated_at": datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 已输出: {user_output_file}")
    
    # 返回（保持原有格式不变）
    return planner, user_profile, next_topic


# ==================== 监控启动函数（新增） ====================

def start_monitor():
    """
    启动监控服务（新增功能，不影响原有函数）
    监控 WATCH_DIR 目录，自动处理新的用户画像文件
    """
    print("="*60)
    print("🚀 启动监控服务")
    print("="*60)
    
    # 初始化知识图谱
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    kg = KnowledgeGraph(KNOWLEDGE_DIR)
    
    # 初始化规划器
    planner = PlannerAgent(kg)
    
    # 初始化监控器
    monitor = UserProfileMonitor(planner, WATCH_DIR, OUTPUT_DIR)
    
    # 添加回调
    def on_path_update(user_profile, learning_path, user_id):
        print(f"[回调] 📢 用户 {user_id} 的学习路径已更新（使用LLM规划）")
        print(f"[回调] 下一步知识点: {learning_path.get('next_step', '无')}")
    
    monitor.add_callback(on_path_update)
    monitor.start()
    
    return monitor


# ==================== 主程序 ====================

if __name__ == "__main__":
    # 原有用法（完全不变）
    # planner, user_profile, next_topic = run_planner(
    #     KNOWLEDGE_DIR="./knowledge",
    #     user_profile={"user_id": "test", "knowledge_level": {}},
    #     output_dir="./output"
    # )
    
    # 新增：启动监控服务
    print("\n启动监控模式...")
    monitor = start_monitor()
    
    print("\n" + "="*60)
    print("✅ 监控服务已启动")
    print(f"📝 监控目录: {WATCH_DIR}")
    print(f"📂 输出目录: {OUTPUT_DIR}")
    print("💡 将用户画像 JSON 文件放入监控目录即可自动生成学习路径")
    print("按 Ctrl+C 停止服务")
    print("="*60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        monitor.stop()
        print("服务已停止")