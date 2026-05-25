import os
import json
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agentplan import KnowledgeGraph, PlannerAgent


# ==================== 配置 ====================

# 获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../.."))

# 知识库目录
MEMORY_PATH = os.path.join(project_root, "data", "knowledge", "memory.json")

# 用户画像目录（从真实文件读取）
PROFILE_DIR = os.path.join(project_root, "data", "profile_outputs")

# 输出目录（测试输出）
OUTPUT_DIR = os.path.join(project_root, "data", "planner")


# ==================== 测试函数 ====================

def load_all_profiles():
    """从 profile_outputs 目录加载所有用户画像"""
    profiles = []
    
    if not os.path.exists(PROFILE_DIR):
        print(f"❌ 用户画像目录不存在: {PROFILE_DIR}")
        return profiles
    
    for filename in os.listdir(PROFILE_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(PROFILE_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    profile = json.load(f)
                
                # 提取 user_id（从文件名或内容）
                user_id = profile.get("user_id")
                if not user_id:
                    user_id = filename.replace(".json", "")
                    profile["user_id"] = user_id
                
                profiles.append(profile)
                print(f"✅ 加载用户画像: {user_id} ({filename})")
            except Exception as e:
                print(f"❌ 加载失败 {filename}: {e}")
    
    return profiles


def test_knowledge_graph():
    """测试知识图谱加载"""
    print("\n" + "=" * 60)
    print("测试1：知识图谱加载")
    print("=" * 60)
    
    if not os.path.exists(MEMORY_PATH):
        print(f"❌ 知识库文件不存在: {MEMORY_PATH}")
        return None
    
    kg = KnowledgeGraph(MEMORY_PATH)  # 传文件路径
    print(f"✅ 加载了 {len(kg.nodes)} 个知识点")
    print(f"✅ 依赖边数量: {kg.graph.number_of_edges()}")
    
    # 打印前5个知识点
    print("\n知识点列表（前5个）:")
    for i, (node_id, node) in enumerate(list(kg.nodes.items())[:5]):
        print(f"   {i+1}. [{node_id}] {node.name} (难度: {node.difficulty})")
        if node.prerequisites:
            prereq_names = [kg.nodes[p].name for p in node.prerequisites if p in kg.nodes]
            print(f"      前置: {', '.join(prereq_names)}")
    
    return kg


def test_user(planner, profile):
    """测试单个用户"""
    user_id = profile.get("user_id", "unknown")
    
    print(f"\n{'='*60}")
    print(f"测试用户: {user_id}")
    print(f"{'='*60}")
    
    # 构建 planner 输入
    planner_input = {
        "user_id": user_id,
        "knowledge_level": profile.get("knowledge_level", {}),
        "weak_points": profile.get("weak_points", []),
        "progress": profile.get("progress", {}),
        "learning_style": profile.get("learning_style", "hybrid"),
        "learning_pace": profile.get("learning_pace", "normal"),
        "error_tags": profile.get("error_tags", []),
        "difficulty": profile.get("difficulty", "medium"),
        "resource_type": profile.get("resource_type", "text")
    }
    
    print(f"输入信息:")
    print(f"   已掌握: {planner_input['progress'].get('completed_topics', [])}")
    print(f"   薄弱点: {planner_input['weak_points']}")
    print(f"   当前学习: {planner_input['progress'].get('current_topic')}")
    print(f"   学习风格: {planner_input['learning_style']}")
    print(f"   学习节奏: {planner_input['learning_pace']}")
    
    # 计算下一个知识点
    next_topic = planner.get_next_topic(planner_input)
    print(f"\n推荐下一个知识点:")
    print(f"   ID: {next_topic['topic_id']}")
    print(f"   名称: {next_topic['name']}")
    print(f"   理解度: {next_topic['understanding']}")
    print(f"   是否复习: {next_topic['is_review']}")
    
    # 获取教学输出
    teaching_output = planner.get_teaching_output(planner_input, next_topic)
    print(f"\n教学策略:")
    print(f"   学习风格: {teaching_output['learning_style']}")
    print(f"   认知水平: {teaching_output['cognitive_level']['level']}")
    print(f"   平均理解度: {teaching_output['cognitive_level']['understanding_avg']}")
    
    # 获取学习路径
    learning_path = planner.get_learning_path(planner_input)
    print(f"\n学习路径:")
    print(f"   学习路径: {learning_path['learning_path'][:5]}...")
    print(f"   当前步骤: {learning_path['current_step']}")
    print(f"   下一步骤: {learning_path['next_step']}")
    
    # 保存输出到文件
    output_file = os.path.join(OUTPUT_DIR, f"{user_id}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "user_id": user_id,
            "current_topic": next_topic,
            "teaching_output": teaching_output,
            "learning_path": learning_path,
            "updated_at": __import__('datetime').datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 输出已保存: {output_file}")
    
    # LLM 规划（可选）
    if planner.llm_enabled:
        print("\n调用 LLM 智能规划...")
        llm_result = planner.plan_with_llm(planner_input)
        if llm_result:
            llm_file = os.path.join(OUTPUT_DIR, f"{user_id}_llm.json")
            with open(llm_file, "w", encoding="utf-8") as f:
                json.dump(llm_result, f, indent=2, ensure_ascii=False)
            print(f"✅ LLM 规划已保存: {llm_file}")
        else:
            print("❌ LLM 规划失败")
    
    return next_topic


def test_error_handling(planner, profile):
    """测试做题错误后的动态调整"""
    user_id = profile.get("user_id", "unknown")
    
    print(f"\n{'='*60}")
    print(f"测试：做题错误动态调整 - 用户 {user_id}")
    print(f"{'='*60}")
    
    # 假设学生在薄弱点上做错了
    weak_points = profile.get("weak_points", [])
    if not weak_points:
        print("该用户没有薄弱点，跳过测试")
        return
    
    error_topic = weak_points[0]
    print(f"模拟学生做错: {error_topic}")
    
    # 构建当前画像
    planner_input = {
        "user_id": user_id,
        "knowledge_level": profile.get("knowledge_level", {}),
        "weak_points": profile.get("weak_points", []),
        "progress": profile.get("progress", {}),
        "learning_style": profile.get("learning_style", "hybrid"),
        "learning_pace": profile.get("learning_pace", "normal"),
        "error_tags": profile.get("error_tags", []),
        "difficulty": profile.get("difficulty", "medium"),
        "resource_type": profile.get("resource_type", "text")
    }
    
    # 更新状态（做题错误后）
    updated_next_topic = planner.update_from_error(planner_input, error_topic)
    
    print(f"错误后重新推荐:")
    print(f"   名称: {updated_next_topic['name']}")
    print(f"   理解度: {updated_next_topic['understanding']}")
    print(f"   是否复习: {updated_next_topic['is_review']}")


def main():
    print("=" * 60)
    print("Planner Agent 测试（从文件读取用户画像）")
    print("=" * 60)
    
    # 1. 测试知识图谱
    kg = test_knowledge_graph()
    if not kg:
        print("❌ 知识图谱加载失败，请检查 data/knowledge/ 目录")
        return
    
    # 2. 创建规划器
    planner = PlannerAgent(kg)
    
    # 3. 加载所有用户画像（从文件）
    print("\n" + "=" * 60)
    print("测试2：加载用户画像文件")
    print("=" * 60)
    
    profiles = load_all_profiles()
    if not profiles:
        print(f"❌ 未找到用户画像文件，请检查 {PROFILE_DIR} 目录")
        print("提示：确保 data/profile_outputs/ 目录下有 .json 文件")
        return
    
    print(f"\n共加载 {len(profiles)} 个用户画像")
    
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 4. 测试每个用户
    for profile in profiles:
        try:
            test_user(planner, profile)
            test_error_handling(planner, profile)
        except Exception as e:
            print(f"❌ 测试用户 {profile.get('user_id', 'unknown')} 失败: {e}")
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()