import os
import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from agentplan import KnowledgeGraph, PlannerAgent

# ==================== 配置 ====================

# 获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../.."))

# 监听目录（别人放用户画像的地方）
WATCH_DIR = os.path.join(project_root, "data", "profile_outputs")

# 输出目录（你的输出）
OUTPUT_DIR = os.path.join(project_root, "data", "planner")
# 已处理的文件记录（避免重复处理）
processed_files = set()

#  路径
KNOWLEDGE_DIR = os.path.join(project_root, "data", "knowledge")
# ==================== 处理函数 ====================

def process_user_profile(filepath: str):
    global planner
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            user_profile = json.load(f)
        
        user_id = user_profile.get("user_id")
        if not user_id:
            filename = os.path.basename(filepath)
            user_id = filename.replace("profile_", "").replace(".json", "")
        
        if not user_id:
            print(f"[跳过] 文件 {filepath} 无法获取 user_id")
            return
        
        print(f"\n[处理] 用户 {user_id}")
        
        # 构建 planner 需要的格式
        planner_input = {
            "user_id": user_id,
            "knowledge_level": user_profile.get("knowledge_level", {}),
            "weak_points": user_profile.get("weak_points", []),
            "progress": {
                "current_topic": user_profile.get("progress", {}).get("current_topic"),
                "completed_topics": user_profile.get("progress", {}).get("completed_topics", [])
            },
            "learning_style": user_profile.get("learning_style", "hybrid"),
            "learning_pace": user_profile.get("learning_pace", "normal"),
            "error_tags": user_profile.get("error_tags", []),
            "difficulty": user_profile.get("difficulty", "medium"),
            "resource_type": user_profile.get("resource_type", "text")
        }
        
        # ✅ 先生成 LLM 规划
        llm_path = None
        if planner.llm_enabled:
            llm_result = planner.plan_with_llm(planner_input)
            if llm_result and "learning_path" in llm_result:
                llm_path = llm_result["learning_path"]
                print(f"[LLM] 规划成功: {llm_path}")
                
                # 保存 llm 文件
                llm_file = os.path.join(OUTPUT_DIR, f"{user_id}_llm.json")
                with open(llm_file, "w", encoding="utf-8") as f:
                    json.dump(llm_result, f, indent=2, ensure_ascii=False)
                print(f"[LLM] 已保存: {llm_file}")
            else:
                print("[LLM] 规划失败，使用规则规划")
        
        # ✅ 构建学习路径（优先使用 LLM 结果）
        if llm_path:
            # 用 LLM 结果构建路径
            learning_path = planner._build_path_response(planner_input, llm_path)
        else:
            # 回退到规则规划
            learning_path = planner._get_learning_path_rule(planner_input)
        
        # 获取下一个知识点
        next_topic = planner.get_next_topic(planner_input)
        
        # 获取用户画像中的 current_topic
        user_current_topic = planner_input.get("progress", {}).get("current_topic")
        
        # 构建 current_topic
        if user_current_topic:
            topic_id = planner.kg.name_to_id.get(user_current_topic)
            understanding = planner_input.get("knowledge_level", {}).get(user_current_topic, 0.0)
            is_review = user_current_topic in planner_input.get("weak_points", [])
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
        
        # 构建 teaching_output
        teaching_output = planner.get_teaching_output(planner_input, next_topic)
        teaching_output["current_topic"] = current_topic_output
        
        # ✅ 输出到主文件（使用 LLM 路径）
        output_file = os.path.join(OUTPUT_DIR, f"{user_id}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "user_id": user_id,
                "current_topic": current_topic_output,
                "teaching_output": teaching_output,
                "learning_path": learning_path,  # ← 使用 LLM 路径
                "updated_at": __import__('datetime').datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"[输出] 已保存: {output_file}")
        print(f"[信息] 当前知识点: {current_topic_output['name']}")
        print(f"[信息] 推荐下一个: {next_topic['name']}")
        if llm_path:
            print(f"[信息] LLM 路径: {llm_path}")
        
    except Exception as e:
        print(f"[错误] 处理 {filepath} 失败: {e}")

# ==================== 文件监听器 ====================

class ProfileHandler(FileSystemEventHandler):
    """监听 profiles 目录，有新文件时自动处理"""
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".json"):
            # 等待文件写入完成
            time.sleep(0.5)
            if event.src_path not in processed_files:
                processed_files.add(event.src_path)
                process_user_profile(event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".json"):
            time.sleep(0.5)
            if event.src_path not in processed_files:
                processed_files.add(event.src_path)
                process_user_profile(event.src_path)


# ==================== 扫描已有文件 ====================

def scan_existing_profiles():
    """启动时扫描已有的用户画像文件"""
    if not os.path.exists(WATCH_DIR):
        os.makedirs(WATCH_DIR, exist_ok=True)
        print(f"[创建] 监听目录: {WATCH_DIR}")
        return
    
    for filename in os.listdir(WATCH_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(WATCH_DIR, filename)
            if filepath not in processed_files:
                processed_files.add(filepath)
                process_user_profile(filepath)


# ==================== 主程序 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("Planner Agent 多用户服务")
    print("=" * 60)
    
    # 初始化 Planner Agent
    current_dir = os.path.dirname(os.path.abspath(__file__))
# 当前文件: backend/agents/agent_plan/run_planner.py
# 向上 3 级到项目根目录，再进入 data/knowledge
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    KNOWLEDGE_DIR = os.path.join(project_root, "data", "knowledge", )
    
    if not os.path.exists(KNOWLEDGE_DIR):
        print(f"[错误] 找不到 KNOWLEDGE: {KNOWLEDGE_DIR}")
        exit(1)
    
    kg = KnowledgeGraph(KNOWLEDGE_DIR)
    planner = PlannerAgent(kg)
    print(f"[初始化] 知识图谱加载完成")
    
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"[输出目录] {OUTPUT_DIR}")
    
    # 确保监听目录存在
    os.makedirs(WATCH_DIR, exist_ok=True)
    print(f"[监听目录] {WATCH_DIR}")
    print("[等待] 等待用户画像文件...")
    
    # 扫描已有文件
    scan_existing_profiles()
    
    # 启动文件监听
    event_handler = ProfileHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[停止] 服务已关闭")
    
    observer.join()