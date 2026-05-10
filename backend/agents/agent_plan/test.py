import json
import os
from datetime import datetime, timedelta

# ==================== 简单的 Planner Agent ====================

class SimplePlanner:
    def __init__(self):
        # 读取 memory.json
        current_dir = os.path.dirname(os.path.abspath(__file__))
        memory_path = os.path.join(current_dir, "memory.json")
        
        with open(memory_path, "r", encoding="utf-8") as f:
            self.kg = json.load(f)
        
        # 构建知识点字典
        self.topics = {topic["id"]: topic for topic in self.kg.get("topics", [])}
        
        # 构建前置依赖
        self.prerequisites = {}
        for topic_id, topic in self.topics.items():
            self.prerequisites[topic_id] = topic.get("prerequisites", [])
    
    def get_learning_order(self, mastered: list, target: str = None):
        """获取学习顺序"""
        all_topics = set(self.topics.keys())
        mastered_set = set(mastered)
        
        # 确定需要学习的知识点
        if target and target in self.topics:
            needed = self._get_dependencies(target)
            needed.add(target)
            needed = needed - mastered_set
        else:
            needed = all_topics - mastered_set
        
        if not needed:
            return []
        
        # 拓扑排序
        return self._topological_sort(list(needed))
    
    def _get_dependencies(self, topic_id: str, visited=None):
        """递归获取所有前置依赖"""
        if visited is None:
            visited = set()
        for prereq in self.prerequisites.get(topic_id, []):
            if prereq not in visited:
                visited.add(prereq)
                self._get_dependencies(prereq, visited)
        return visited
    
    def _topological_sort(self, topic_ids):
        """简单的拓扑排序"""
        if not topic_ids:
            return []
        
        # 构建依赖计数
        in_degree = {tid: 0 for tid in topic_ids}
        graph = {tid: [] for tid in topic_ids}
        
        for tid in topic_ids:
            for prereq in self.prerequisites.get(tid, []):
                if prereq in topic_ids:
                    graph[prereq].append(tid)
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
        
        # 剩余的追加
        for tid in topic_ids:
            if tid not in result:
                result.append(tid)
        
        return result
    
    def generate_plan(self, mastered: list, weak_points: list = None, target: str = None):
        """生成学习计划"""
        if weak_points is None:
            weak_points = []
        
        # 获取学习顺序
        order = self.get_learning_order(mastered, target)
        
        # 将薄弱点提前
        weak_in_order = [t for t in order if t in weak_points]
        others = [t for t in order if t not in weak_points]
        final_order = weak_in_order + others
        
        # 生成带名称的路径
        path_details = []
        for tid in final_order:
            topic = self.topics.get(tid, {})
            path_details.append({
                "id": tid,
                "name": topic.get("name", tid),
                "difficulty": topic.get("difficulty", "medium")
            })
        
        # 生成每日计划（简单版本）
        daily_plan = self._make_daily_plan(final_order)
        
        # 生成资源推荐
        resources = self._recommend_resources(final_order, weak_points)
        
        return {
            "learning_path": final_order,
            "path_details": path_details,
            "daily_plan": daily_plan,
            "resources": resources,
            "total_topics": len(final_order)
        }
    
    def _make_daily_plan(self, order):
        """生成每日计划"""
        if not order:
            return []
        
        # 每天2个知识点
        daily = []
        day = 1
        for i in range(0, len(order), 2):
            day_topics = order[i:i+2]
            daily.append({
                "day": day,
                "topics": day_topics,
                "topics_name": [self.topics.get(t, {}).get("name", t) for t in day_topics]
            })
            day += 1
        return daily
    
    def _recommend_resources(self, order, weak_points):
        """推荐资源"""
        resources = []
        for tid in order[:5]:  # 只推荐前5个
            topic = self.topics.get(tid, {})
            rec = {
                "topic_id": tid,
                "topic_name": topic.get("name", tid),
                "resources": []
            }
            
            # 文本资源
            if topic.get("content", {}).get("explanation"):
                rec["resources"].append({
                    "type": "text",
                    "title": f"{topic.get('name', tid)} - 文字讲解",
                    "content": topic["content"]["explanation"][:100] + "..."
                })
            
            # 练习题
            questions = topic.get("questions", [])
            if questions:
                rec["resources"].append({
                    "type": "exercise",
                    "title": f"{topic.get('name', tid)} - 练习题",
                    "question": questions[0].get("question", "")
                })
            
            # 常见错误提醒
            if tid in weak_points and topic.get("common_mistakes"):
                rec["resources"].append({
                    "type": "warning",
                    "title": "⚠️ 常见错误提醒",
                    "content": ", ".join(topic["common_mistakes"])
                })
            
            resources.append(rec)
        return resources


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("🎓 Planner Agent 测试程序")
    print("=" * 60)
    
    # 创建 agent
    agent = SimplePlanner()
    
    # 模拟用户数据
    mastered = ["os_mem_01", "os_mem_02"]  # 已掌握地址空间和分页概念
    weak_points = ["os_mem_04"]            # 页表是薄弱点
    target = "os_mem_10"                  # 目标是虚拟内存
    
    print(f"\n📊 用户画像:")
    print(f"   已掌握: {mastered}")
    print(f"   薄弱点: {weak_points}")
    print(f"   学习目标: {target}")
    
    # 生成计划
    result = agent.generate_plan(mastered, weak_points, target)
    
    # ========== 输出结果 ==========
    
    print("\n" + "=" * 60)
    print("📋 学习路径")
    print("=" * 60)
    
    for i, detail in enumerate(result["path_details"], 1):
        print(f"   {i}. {detail['name']} ({detail['id']}) - 难度: {detail['difficulty']}")
    
    print("\n" + "=" * 60)
    print("📅 学习计划")
    print("=" * 60)
    
    for day in result["daily_plan"]:
        print(f"\n   第{day['day']}天:")
        for name in day["topics_name"]:
            print(f"      - {name}")
    
    print("\n" + "=" * 60)
    print("📚 资源推荐")
    print("=" * 60)
    
    for rec in result["resources"]:
        print(f"\n   【{rec['topic_name']}】")
        for res in rec["resources"]:
            print(f"      [{res['type']}] {res['title']}")
    
    print("\n" + "=" * 60)
    print(f"✅ 规划完成！共 {result['total_topics']} 个知识点需要学习")
    print("=" * 60)