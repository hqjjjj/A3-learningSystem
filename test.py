# test.py
import sys
import os

# 把 agent_profile 目录加到系统路径，这样才能导入 profile_agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'agents', 'agent_profile'))

import json
from profile_agent import ProfileAgent

# 初始化 Agent（换成你自己的凭证）
agent = ProfileAgent(
    app_id="nide",
    api_key="nide",
    api_secret="nide"
)

# ============================================
# 在这里改你的测试数据
# ============================================

# 测试用户ID
user_id = "test_stu_001"

# 模拟第一次对话
print("=" * 60)
print("📝 第一次对话：初始构建画像")
print("=" * 60)
result1 = agent.build_profile(
    user_id=user_id,
    user_input="我计算机专业大三，在学操作系统，分页机制完全不会，我喜欢看视频学。"
)
print(result1.profile.model_dump_json(indent=2))

# 模拟第二次对话（带行为数据）
print("\n" + "=" * 60)
print("📝 第二次对话：增量更新画像")
print("=" * 60)
result2 = agent.build_profile(
    user_id=user_id,
    user_input="缺页中断还是搞不懂，做题正确率很低。",
    behavior={"correct_rate": 0.3, "recent_actions": ["错题:缺页中断"]}
)
print(result2.profile.model_dump_json(indent=2))

# 模拟第三次对话
print("\n" + "=" * 60)
print("📝 第三次对话：继续更新画像")
print("=" * 60)
result3 = agent.build_profile(
    user_id=user_id,
    user_input="今天学了虚拟内存，感觉比缺页中断简单，正确率上来了。",
    behavior={"correct_rate": 0.75, "recent_actions": ["完成练习:虚拟内存"]}
)
print(result3.profile.model_dump_json(indent=2))