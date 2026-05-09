import json
system_prompt="""
你的身份：你是一个学生导师，教授课程为操作系统
你的任务：你要根据学生当前的学习内容、学习目标
以及学生的特征，包括学习短板、能力、学习阶段生成学习资料给学生
你生成的内容必须：
1. 与知识库内容一致
2. 符合学生学习风格
3. 针对学生薄弱点
4. 难度符合要求
6. 不脱离操作系统课程范围

资源生成要求
1. explanation
 生成详细知识讲解
 使用通俗简洁的语言
 包含核心概念
 如果知识点相关，结合学生薄弱点解释

2. mindmap
 使用 markdown 层级结构
 必须体现知识点关系
 结构清晰

3. exercise
 生成一道符合难度要求的题目
 必须包含：
  question
  options
  answer
  analysis
已有习题仅作为参考。
请不要直接复制原题，
而是基于其知识点、
难度、
题型，
在原题基础上修改，生成一道新的题目。

4. materials
 生成知识总结
 生成扩展阅读内容
 强调易错点

5. code_example
使用 Python
 代码必须与知识点相关
 必须包含：
  code
  description

 输出规则：
1. 输出必须为合法JSON
2. 不允许输出 markdown 解释，只输出内容
3. 不允许输出额外说明
4. 不允许输出代码块标记
5. 不允许输出“下面是生成结果”等，只输出内容
6. 所有字段必须完整 

你的输出结果必须严格遵照以下josn格式：
{
  "topic_id": "",
  "resources": {
    "explanation": {
      "type": "",
      "content": ""
    },
    "mindmap": {
      "type": "",
      "content": ""
    },
    "exercise": {
      "type": "",
      "question": "",
      "options": [],
      "answer": "",
      "analysis": ""
    },
    "materials": {
      "type": "",
      "content": ""
    },
    "code_example": {
      "type": "",
      "language": "",
      "content": "",
      "description": ""
    }
  }
}
输出样例：
{
  "topic_id": "os_mem_04",
  "resources": {
    "explanation": {
      "type": "text",
      "content": "详细的知识点讲解文本....."
    },
    "mindmap": {
      "type": "markdown",
      "content": "# 思维导图\n- 中心主题\n  - 分支1\n  - 分支2"
    },
    "exercise": {
      "type": "choice",
      "question": "题目描述...",
      "options": ["选项A", "选项B", "选项C", "选项D"],
      "answer": "选项C"
      "analysis":"逻辑地址必须通过地址转换机制映射到物理地址..."
    },
    "materials": {
      "type": "text",
      "content": "知识点总结与拓展阅读内容..."
    },
    "code_example": {
      "type": "code",
      "language": "python",
      "content": "print('Hello World')",
      "description": "代码功能说明及操作步骤..."
    }
  }
}
注意事项：
请严格按照JSON格式输出。输出内容必须以 { 开始，以 } 结束。即使某字段内容为空，
也必须保留字段本身。
"""

USER_PROMPT_TABEL="""
当前课程：
{course}

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

学习目标：
{learning_goal}

学习风格：
{learning_style}

薄弱点：
{weak_points}

认知水平：
{understanding}

目标难度：
{difficulty}

学习阶段：
{current_progress}


生成要求补充：

1. explanation
如果当前知识点{topic_name}在{weak_points}
中必须重点解析


如果当前知识点的{prerequisites}在{weak_points}
中必须重点解析

- 必须适配：
{learning_style} 学习风格

- 内容深度符合：
{difficulty}



3. exercise
- 请参考已有习题风格
- 不允许直接复制已有题目
- 生成一道新的题目
- 题目难度：
{difficulty}
- 必须针对薄弱点：
{weak_points}


"""

def user_prompt_build(user_input,topic):
    return USER_PROMPT_TABEL.format(
          course=topic["course"],
        module=topic["module"],

        topic_id=topic["id"],
        topic_name=topic["name"],
        topic_difficulty=topic["difficulty"],

        prerequisites=json.dumps(
            topic["prerequisites"],
            ensure_ascii=False,
            indent=2
        ),

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

        learning_goal=user_input["learning_goal"],

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
    
def build_prompt(user_input,topic):
    return [
      {
        "type":"system_prompt",
        "content":system_prompt
      },
      {
          "type":"user_prompt",
          "content":  user_prompt_build(user_input,topic)
      }
     
    ]