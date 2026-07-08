import json
def build_kn_prompt(alloweds,module, topic_name):
    base_quote = f"源于教材知识库：《{module}》{topic_name}"

    schema = {}

    if "explanation" in alloweds:
        schema["explanation"] = {
            "type":"text",
             "title":"",
            "content":"",
            "knowledge_base_quote": [base_quote, "具体引用的解释原句..."]
        }

    if "mindmap" in alloweds:
        schema["mindmap"] = {
            "type":"markdown",
             "title":"",
            "content":"# 中心主题\n## 分支1\n- 要点1\n- 要点2\n## 分支2\n...",
            "knowledge_base_quote": [base_quote, "具体引用的解释原句..."]
        }

    if "materials" in alloweds:
        schema["materials"] = {
            "type":"text",
             "title":"",
            "content":"",
            "knowledge_base_quote": [base_quote, "具体引用的解释原句..."]
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
严格根据知识库内容与学生画像，
生成知识讲解类学习资源。

**重要**：你必须且只能生成以下资源类型：{alloweds}

禁止生成其他资源。

输出规则：
1. 输出必须为合法JSON
2. 只输出JSON
3. 禁止输出未请求资源
4.每个资源对象必须包含 type、title、content 字段。
    - type 固定为 "text"（对 explanation/materials）或 "markdown"（对 mindmap）
    - title 不能为空，要能概括该资源内容。
    - content 不能为空。
    - **对于 mindmap，content 必须使用 Markdown 格式，包含至少一个一级标题（#）、若干二级标题（##）和列表（-），以清晰展示层次结构。**
**重要**：每个资源对象必须包含 `knowledge_base_quote` 字段（字符串数组），且**第一个元素必须严格为 `"{base_quote}"`**，其中 `{base_quote}` 是系统传入的固定格式，不得自行更改或编造。后续元素填写你依据的原文，整个数组不超过三个元素。
输出格式：
{schema_str}
"""