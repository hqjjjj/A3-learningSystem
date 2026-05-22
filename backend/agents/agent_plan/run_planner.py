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
WATCH_DIR = os.path.join(project_root, "data", "profiles")

# 输出目录（你的输出）
OUTPUT_DIR = os.path.join(project_root, "data", "paths")
# 已处理的文件记录（避免重复处理）
processed_files = set()

# memory.json 路径
MEMORY_PATH = os.path.join(project_root, "data", "knowledge", "memory.json")
# ==================== 处理函数 ====================

def process_user_profile(filepath: str):
    """处理单个用户画像文件"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            user_profile = json.load(f)
        
        user_id = user_profile.get("user_id")
        if not user_id:
            print(f"[跳过] 文件 {filepath} 缺少 user_id")
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
        
        # 调用 Planner Agent
        next_topic = planner.get_next_topic(planner_input)
        teaching_output = planner.get_teaching_output(planner_input, next_topic)
        learning_path = planner.get_learning_path(planner_input)
        
        # 输出到 data/paths/{user_id}.json
        output_file = os.path.join(OUTPUT_DIR, f"{user_id}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "user_id": user_id,
                "current_topic": next_topic,
                "teaching_output": teaching_output,
                "learning_path": learning_path,
                "updated_at": __import__('datetime').datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"[输出] 已保存: {output_file}")
        
        # 可选：调用 LLM 生成额外规划
        if planner.llm_enabled:
            llm_result = planner.plan_with_llm(planner_input)
            if llm_result:
                llm_file = os.path.join(OUTPUT_DIR, f"{user_id}_llm.json")
                with open(llm_file, "w", encoding="utf-8") as f:
                    json.dump(llm_result, f, indent=2, ensure_ascii=False)
                print(f"[LLM] 已保存: {llm_file}")
        
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
# 向上 3 级到项目根目录，再进入 data/knowledge/memory.json
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    memory_path = os.path.join(project_root, "data", "knowledge", "memory.json")
    
    if not os.path.exists(memory_path):
        print(f"[错误] 找不到 memory.json: {memory_path}")
        exit(1)
    
    kg = KnowledgeGraph(memory_path)
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