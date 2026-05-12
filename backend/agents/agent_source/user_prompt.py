import json
USER_PROMPT_TABEL="""
当前课程：
操作系统

当前模块：
{module}

当前知识点：

知识点ID：
{topic_id}

知识点名称：
{topic_name}

知识点难度：
{topic_difficulty}

前置知识：
{prerequisites}

知识点解释：
{explanation}

知识点示例：
{example}

知识点总结：
{summary}

常见错误：
{common_mistakes}

已有习题：
{questions}



学生画像：



学习风格：
{learning_style}

薄弱点：
{weak_points}

认知水平：
{understanding}

目标难度：
{difficulty}

当前学习阶段：
{current_progress}

生成资源类型：
{resource_type}

生成要求补充：

1. explanation
如果当前知识点{topic_name}在{weak_points}
中必须重点解析


如果当前知识点的{prerequisites}在{weak_points}
中必须重点解析

- 内容难度符合：
{difficulty}



3. exercise
- 请参考已有习题风格
- 不允许直接复制已有题目
- 生成一道新的题目
- 题目难度：
{difficulty}
- 必须针对薄弱点：
{weak_points}
- 必须适配：
{learning_style} 题目类型

"""

def user_prompt_build(user_input,topic,kb):
    prereq_names = []
    for pid in topic["prerequisites"]:
        prereq_topic = kb.get_topic_by_id(pid)
        if prereq_topic:
            prereq_names.append(prereq_topic["name"])
        else:
            prereq_names.append(pid)
    prereq_names_str = json.dumps(prereq_names, ensure_ascii=False, indent=2)
    return USER_PROMPT_TABEL.format(
        module=user_input["module"],

        topic_id=topic["id"],
        topic_name=topic["name"],
        topic_difficulty=topic["difficulty"],

        prerequisites=prereq_names_str,

        explanation=topic["content"]["explanation"],

        example=topic["content"]["example"],

        summary=topic["content"]["summary"],

        common_mistakes=json.dumps(
            topic["common_mistakes"],
            ensure_ascii=False,
            indent=2
        ),

        questions=json.dumps(
            topic["questions"],
            ensure_ascii=False,
            indent=2
        ),

        
        resource_type=user_input["resource_type"],
        learning_style=user_input["learning_style"],

        weak_points=json.dumps(
            user_input["weak_points"],
            ensure_ascii=False,
            indent=2
        ),

        understanding=user_input["understanding"],

        difficulty=user_input["difficulty"],
        current_progress=user_input["current_progress"]
    )
    

     
    