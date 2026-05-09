# 学习画像构建Agent

软件杯A3赛题 - 基于大模型的个性化资源生成与学习多智能体系统

## 模块说明

本模块负责**对话式学习画像自主构建**，通过自然语言对话自动提取学生特征，构建结构化动态画像，为后续路径规划和资源生成提供用户模型基础。

## 核心功能

- 对话式特征提取：从自然语言中提取专业、年级、课程、薄弱知识点等
- 知识图谱对齐：画像知识点与课程知识图谱精准匹配
- 动态增量更新：支持画像随学随新，已掌握信息不丢失
- 认知风格识别：visual/textual/auditory 三向量量化分布
- 学习节奏推断：fast/normal/slow 自适应调整

## 画像输出维度（7个）

| 维度 | 说明 |
|------|------|
| knowledge_level | 各知识点掌握度(0-1) |
| weak_points | 薄弱知识点列表 |
| error_tags | 高频错误标签 |
| cognitive_style | 认知风格量化分布 |
| learning_pace | 学习节奏 |
| preference | 资源偏好与难度 |
| progress | 学习进度追踪 |

## 启动方式

\`\`\`bash
pip install -r requirements.txt
python api_server.py
\`\`\`

服务启动后访问 http://127.0.0.1:8000/docs 查看接口文档。

## 接口说明

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/profile/build | POST | 构建/更新画像 |
| /api/profile/{user_id} | GET | 查询学生画像 |
| /api/profiles | GET | 查看所有画像 |

## 作者

Team A3 - UserModelingAgent