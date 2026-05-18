# test.py
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'agents', 'agent_profile'))

from profile_agent import ProfileAgent

agent = ProfileAgent(
    app_id="nide",
    api_key="nide",
    api_secret="nide"
)

# 项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))

# 多用户测试数据
users = [
    {
        "user_id": "stu_001",
        "user_input": "我计算机大三，操作系统分页不会，喜欢看视频",
        "behavior": {"correct_rate": 0.5}
    },
    {
        "user_id": "stu_002",
        "user_input": "我软件工程大二，数据结构二叉树遍历搞不懂，喜欢看文档",
        "behavior": {"correct_rate": 0.4}
    },
    {
        "user_id": "stu_003",
        "user_input": "我人工智能研一，学虚拟内存和缺页中断，正确率很高",
        "behavior": {"correct_rate": 0.85}
    }
]

for user in users:
    result = agent.build_profile(
        user_id=user["user_id"],
        user_input=user["user_input"],
        behavior=user.get("behavior")
    )
    
    # 每个用户单独输出一个 JSON 文件
    output_path = os.path.join(project_root, "data", "profile_outputs", f"profile_{user['user_id']}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result.profile.model_dump_json(indent=2))
    
    print(f"✅ {user['user_id']} 画像已保存到 {output_path}")