import json
def build_kn_prompt(alloweds):

    schema = {}

    if "explanation" in alloweds:
        schema["explanation"] = {
            "type":"text",
            "content":""
        }

    if "mindmap" in alloweds:
        schema["mindmap"] = {
            "type":"markdown",
            "content":""
        }

    if "materials" in alloweds:
        schema["materials"] = {
            "type":"text",
            "content":""
        }

    schema_str = json.dumps(
        schema,
        ensure_ascii=False,
        indent=2
    )

    return f"""
你的身份：
你是一个操作系统课程导师。

你的任务：
根据知识库内容与学生画像，
生成知识讲解类学习资源。

只允许生成：
{alloweds}

禁止生成其他资源。

输出规则：
1. 输出必须为合法JSON
2. 只输出JSON
3. 禁止输出未请求资源

输出格式：
{schema_str}
"""