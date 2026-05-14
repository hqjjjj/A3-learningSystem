import json
import os
from agentplan import KnowledgeGraph, PlannerAgent, save_json, run_planner

# ==================== 测试数据 ====================

# 模拟用户画像（从图片中提取的真实数据）
test_user_profile = {
    "user_id": "test_stu_001",
    "major": "计算机",
    "grade": "大三",
    "course": "操作系统",
    "knowledge_level": {
        "分页基本概念": 0.45,
        "缺页中断": 0.25,
        "虚拟内存": 0.45
    },
    "weak_points": ["缺页中断"],
    "error_tags": [],
    "learning_style": "diagram",
    "cognitive_style": {
        "visual": 0.7,
        "textual": 0.15,
        "auditory": 0.15
    },
    "learning_pace": "normal",
    "resource_type": "exercise",
    "difficulty": "hard",
    "progress": {
        "current_topic": "虚拟内存",
        "completed_topics": []
    },
    "learning_goal": None,
    "created_at": "2026-05-11T20:59:57.359796",
    "updated_at": "2026-05-11T21:00:14.359359"
}

# 测试数据2：做题错误后的场景
test_user_profile_with_error = {
    "user_id": "test_stu_001",
    "major": "计算机",
    "grade": "大三",
    "course": "操作系统",
    "knowledge_level": {
        "地址空间基本概念": 0.85,
        "分页基本概念": 0.65,
        "页表": 0.25,
        "缺页中断": 0.05,
        "虚拟内存": 0.45
    },
    "weak_points": ["缺页中断", "页表"],
    "error_tags": ["不理解缺页中断触发时机"],
    "learning_style": "diagram",
    "cognitive_style": {"visual": 0.7, "textual": 0.15, "auditory": 0.15},
    "learning_pace": "normal",
    "resource_type": "video",
    "difficulty": "medium",
    "progress": {
        "current_topic": None,
        "completed_topics": ["os_mem_01"]
    },
    "learning_goal": "虚拟内存"
}


# ==================== 运行测试 ====================

def main():
    # 路径设置
    current_dir = os.path.dirname(os.path.abspath(__file__))
    memory_path = os.path.join(current_dir, "memory.json")
    output_dir = current_dir
    
    print("=" * 60)
    print("Planner Agent 测试")
    print("=" * 60)
    
    # 测试1：正常场景
    print("\n【测试1】正常用户画像")
    print("-" * 40)
    
    kg = KnowledgeGraph(memory_path)
    planner = PlannerAgent(kg)
    
    # 输出知识图谱
    save_json(kg.to_json(), os.path.join(output_dir, "knowledge_graph.json"))
    
    # 计算下一个知识点
    next_topic = planner.get_next_topic(test_user_profile)
    print(f"\n下一个知识点: {next_topic}")
    
    # 输出给资源生成模块
    teaching_output = planner.get_teaching_output(test_user_profile, next_topic)
    save_json(teaching_output, os.path.join(output_dir, "teaching_output.json"))
    
    # 输出学习路径
    learning_path = planner.get_learning_path(test_user_profile)
    save_json(learning_path, os.path.join(output_dir, "learning_path.json"))
    
    # 测试2：做题错误后动态调整
    print("\n" + "=" * 60)
    print("【测试2】做题错误动态调整")
    print("-" * 40)
    
    error_topic = "缺页中断"
    print(f"\n学生做错: {error_topic}")
    
    updated_profile = planner.update_from_error(test_user_profile, error_topic)
    
    new_next_topic = planner.get_next_topic(updated_profile)
    print(f"\n重新规划后的下一个知识点: {new_next_topic}")
    
    new_teaching_output = planner.get_teaching_output(updated_profile, new_next_topic)
    save_json(new_teaching_output, os.path.join(output_dir, "teaching_output_after_error.json"))
    
    # 测试3：完整学习路径
    print("\n" + "=" * 60)
    print("【测试3】完整学习路径")
    print("-" * 40)
    
    learning_path_result = planner.get_learning_path(updated_profile)
    print(f"\n学习路径: {learning_path_result['learning_path']}")
    print(f"当前步骤: {learning_path_result['current_step']}")
    print(f"下一步骤: {learning_path_result['next_step']}")
    
    # 测试4：LLM 规划（如果启用）
    if planner.llm_enabled:
        print("\n" + "=" * 60)
        print("【测试4】LLM 智能规划")
        print("-" * 40)
        
        llm_result = planner.plan_with_llm(test_user_profile)
        if llm_result:
            save_json(llm_result, os.path.join(output_dir, "llm_plan.json"))
            print(f"\nLLM 规划结果: {llm_result}")
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()