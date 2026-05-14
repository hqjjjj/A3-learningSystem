学习画像构建 Agent 接口文档
概述
本模块负责对话式学习画像自主构建，通过自然语言对话自动提取学生特征，输出标准化 JSON 画像，供路径规划 Agent 和资源生成 Agent 调用。

启动服务
bash
cd backend/agents/agent_profile
python api_server.py
服务地址：http://127.0.0.1:8000

API 文档页面：http://127.0.0.1:8000/docs

接口列表
1. 构建/更新画像
POST /api/profile/build

请求体：

json
{
  "user_id": "stu_001",
  "user_input": "我计算机大三，操作系统分页不会，喜欢看视频学",
  "history": [],
  "behavior": {
    "correct_rate": 0.5,
    "recent_actions": ["错题:分页"]
  }
}
字段	类型	必填	说明
user_id	string	是	学生唯一标识
user_input	string	是	学生对话内容
history	list	否	历史对话记录
behavior	object	否	行为数据
behavior.correct_rate	float	否	做题正确率(0-1)
behavior.recent_actions	list	否	最近行为列表
返回示例：

json
{
  "profile": {
    "user_id": "stu_001",
    "major": "计算机",
    "grade": "大三",
    "course": "操作系统",
    "knowledge_level": {
      "地址空间基本概念": 0.0,
      "分页基本概念": 0.45,
      "地址结构（页号+偏移）": 0.0,
      "页表": 0.0,
      "快表（TLB）": 0.0,
      "缺页中断": 0.0,
      "页面置换算法": 0.0,
      "内部碎片": 0.0,
      "外部碎片": 0.0,
      "虚拟内存": 0.0
    },
    "weak_points": [],
    "error_tags": [],
    "learning_style": "diagram",
    "cognitive_style": {
      "visual": 0.7,
      "textual": 0.15,
      "auditory": 0.15
    },
    "learning_pace": "normal",
    "resource_type": ["explanation"],
    "difficulty": "medium",
    "progress": {
      "current_topic": "分页基本概念",
      "completed_topics": []
    },
    "learning_goal": null
  },
  "update_type": "init",
  "confidence": 0.85
}
2. 查询学生画像
GET /api/profile/{user_id}

示例： GET /api/profile/stu_001

返回： 同上 profile 对象

3. 查看所有画像（调试用）
GET /api/profiles

字段说明
字段	类型	说明
user_id	string	学生唯一标识
major	string	专业
grade	string	年级
course	string	当前课程
knowledge_level	object	各知识点掌握度(0.0-1.0)，0.0表示未学
weak_points	list	薄弱知识点（0.0 < 分数 ≤ 0.3）
error_tags	list	高频错误标签（0.0 < 分数 ≤ 0.2）
learning_style	string	text(文本型) 或 diagram(图解型)
cognitive_style	object	认知风格三向量，和为1
learning_pace	string	fast / normal / slow
resource_type	list	偏好资源类型：explanation、mindmap、exercise、code_example
difficulty	string	偏好难度：easy / medium / hard
progress.current_topic	string	当前学习主题
progress.completed_topics	list	已完成主题列表
update_type	string	init(首次) 或 update(更新)
confidence	float	画像置信度(0-1)
调用示例（Python）
python
import requests

# 构建画像
resp = requests.post("http://127.0.0.1:8000/api/profile/build", json={
    "user_id": "stu_001",
    "user_input": "分页机制搞不懂，做题总错",
    "behavior": {"correct_rate": 0.3}
})
profile = resp.json()["profile"]

# 路径规划 Agent 直接读取
current_topic = profile["progress"]["current_topic"]
knowledge = profile["knowledge_level"]
weak_points = profile["weak_points"]