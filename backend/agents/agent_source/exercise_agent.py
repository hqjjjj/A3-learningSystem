#输入参数定义
from backend.agents.agent_source.exercise_prompt import system_prompt_exercise
from backend.agents.agent_source.user_prompt import user_prompt_build
from data.knowledge.KnowledgeBaseManager import KnowledgeBaseManager
from backend.agents.agent_source.lmm import SparkLLM
import json
import os
from json_repair import repair_json

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../..")
)
kb = KnowledgeBaseManager(
    os.path.join(BASE_DIR, "data/knowledge")
)
llm=SparkLLM()

def parse_output(result):

    fixed = repair_json(result)

    try:
        return json.loads(fixed)

    except Exception as e:
        return {
            "raw": result,
            "fixed": fixed,
            "error": str(e)
        }
def build_prompt(user_input,topic,kb):
    return system_prompt_exercise, user_prompt_build(user_input, topic,kb)   
class agentexercise:
    # system和user 双层结构
    #需要从知识库传递一整个topic内容
    def run(self,input_data,topic):
        
        system, user = build_prompt(input_data, topic,kb)
        for i in range(3):
            result = llm.generate(system, user)
            result= parse_output(result)
            if "error" not in result:
                # ========== 1. 标准化：确保得到练习对象 ==========
                ex_obj = {}

                # 情况A：LLM 正确返回 {"exercise": {...}}
                if "exercise" in result and isinstance(result["exercise"], dict):
                    ex_obj = result["exercise"]
                else:
                    # 情况B：LLM 直接返回了练习内容（无 exercise 包装）或格式错误
                    # 尝试从 result 中提取可能字段，构造一个基础练习对象
                    ex_obj = {
                        "type": result.get("type", "short"),
                        "title": result.get("title", f"{input_data.get('module', '练习')}题"),
                        "question": result.get("question") or result.get("content", "题目暂缺"),
                        "options": result.get("options", []),
                        "answer": result.get("answer", ""),
                        "analysis": result.get("analysis", "")
                    }

                # ========== 2. 补全必填字段 ==========
                ex_obj.setdefault("type", "short")
                ex_obj.setdefault("title", f"{input_data.get('module', '练习')}题")
                ex_obj.setdefault("question", "题目暂缺")
                ex_obj.setdefault("answer", "")
                ex_obj.setdefault("analysis", "")
                # options 单独处理：如果 type 已经是 short 但存在 options，则删除；如果是 choice 则确保数组
                if "options" not in ex_obj:
                    ex_obj["options"] = [] if ex_obj["type"] == "short" else []

                # ========== 3. 智能修正 type ==========
                current_type = ex_obj.get("type", "")
                if current_type not in ("choice", "short"):
                    # 根据 options 是否非空判断
                    if ex_obj.get("options") and len(ex_obj["options"]) > 0:
                        ex_obj["type"] = "choice"
                    else:
                        ex_obj["type"] = "short"

                # ========== 4. 根据最终 type 清理 options 和 answer ==========
                if ex_obj["type"] == "choice":
                    # 选择题必须保证 options 非空
                    if not ex_obj["options"]:
                        ex_obj["options"] = ["选项A", "选项B"]  # 占位
                    # answer 应为选项内容（不是字母），如果 answer 是 "A" 之类，尝试匹配
                    answer_val = ex_obj.get("answer", "")
                    if answer_val and len(answer_val) == 1 and answer_val.isalpha():
                        idx = ord(answer_val.upper()) - ord('A')
                        if 0 <= idx < len(ex_obj["options"]):
                            ex_obj["answer"] = ex_obj["options"][idx]
                else:  # short
                    # 简答题不应有 options 字段
                    ex_obj.pop("options", None)
                    # 确保 answer 至少是一个字符串（可能为空）

                # ========== 5. 最终强制修正（解决 LLM 输出 "exercise" 等非法 type） ==========
                # 再次确认 type 是否为 "choice" 或 "short"
                if ex_obj.get("type") not in ("choice", "short"):
                    if ex_obj.get("options") and len(ex_obj.get("options", [])) > 0:
                        ex_obj["type"] = "choice"
                    else:
                        ex_obj["type"] = "short"

                # 如果 question 字段缺失或为空，尝试从 content 中提取（降级方案）
                if not ex_obj.get("question"):
                    # 如果存在 content，将其作为问题（可能包含 Markdown）
                    ex_obj["question"] = ex_obj.get("content", "题目暂缺")
                    # 删除 content 字段，避免前端混淆
                    ex_obj.pop("content", None)

                # 确保 short 类型没有 options 字段
                if ex_obj["type"] == "short":
                    ex_obj.pop("options", None)

                # 确保 choice 类型有 options 且 answer 是选项内容
                if ex_obj["type"] == "choice":
                    if not ex_obj.get("options"):
                        ex_obj["options"] = ["选项A", "选项B"]
                    # 如果 answer 仍是字母，再做一次转换
                    answer_val = ex_obj.get("answer", "")
                    if answer_val and len(answer_val) == 1 and answer_val.isalpha():
                        idx = ord(answer_val.upper()) - ord('A')
                        if 0 <= idx < len(ex_obj["options"]):
                            ex_obj["answer"] = ex_obj["options"][idx]

                # ========== 6. 最终包装 ==========

                module = input_data.get("module", "未知章节")
                topic_name = topic.get("name", "未知知识点")
                base_citation = f"源于教材知识库：《{module}》{topic_name}"

                if "knowledge_base_quote" not in ex_obj or not ex_obj["knowledge_base_quote"]:
                    ex_obj["knowledge_base_quote"] = [base_citation]
                else:
                    if not ex_obj["knowledge_base_quote"][0].startswith("源于教材知识库"):
                        ex_obj["knowledge_base_quote"].insert(0, base_citation)
                        
                return {"exercise": ex_obj}
            else:
                user+=f"""
            你刚才输出的JSON不合法。
            请重新输出合法JSON。
            错误：
            {result["error"]}
                """  
        return {
        "error":"retry failed"
         }

