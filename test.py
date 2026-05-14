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
result1 = agent.build_profile(
    user_id=user_id,
    user_input="我计算机专业大三，在学操作系统。分页机制完全不会，喜欢看视频。缺页中断做题正确率很低。虚拟内存感觉简单一些，正确率上来了。",
    behavior={"correct_rate": 0.5}
)
print(result1.profile.model_dump_json(indent=2))

# 保存成 JSON 文件
output_path = os.path.join(project_root, "data", "profile_output.json")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(result1.profile.model_dump_json(indent=2))
print("已保存到 profile_output.json")