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
                #  标准化：确保得到练习对象 
                ex_obj = {}
                if "exercise" in result and isinstance(result["exercise"], dict):
                    ex_obj = result["exercise"]
                else:
                    ex_obj = {
                        "type": result.get("type", "short"),
                        "title": result.get("title", f"{input_data.get('module', '练习')}题"),
                        "question": result.get("question") or result.get("content", "题目暂缺"),
                        "options": result.get("options", []),
                        "answer": result.get("answer", ""),
                        "analysis": result.get("analysis", "")
                    }

                #  补全必填字段 
                ex_obj.setdefault("type", "short")
                ex_obj.setdefault("title", f"{input_data.get('module', '练习')}题")
                ex_obj.setdefault("question", "题目暂缺")
                ex_obj.setdefault("answer", "")
                ex_obj.setdefault("analysis", "")
                # options 单独处理：如果 type 已经是 short 但存在 options，则删除；如果是 choice 则确保数组
                if "options" not in ex_obj:
                    ex_obj["options"] = [] if ex_obj["type"] == "short" else []

                #  智能修正 type 
                current_type = ex_obj.get("type", "")
                if current_type not in ("choice", "short"):
                    if ex_obj.get("options") and len(ex_obj["options"]) > 0:
                        ex_obj["type"] = "choice"
                    else:
                        ex_obj["type"] = "short"

                # 根据最终 type 清理 options 和 answer 
                if ex_obj["type"] == "choice":
                    # 选择题必须保证 options 非空
                    if not ex_obj["options"]:
                        ex_obj["options"] = ["选项A", "选项B"]  # 占位
                    answer_val = ex_obj.get("answer", "")
                    if answer_val and len(answer_val) == 1 and answer_val.isalpha():
                        idx = ord(answer_val.upper()) - ord('A')
                        if 0 <= idx < len(ex_obj["options"]):
                            ex_obj["answer"] = ex_obj["options"][idx]
                else:  
                    ex_obj.pop("options", None)


                # 一系列修正
                if ex_obj.get("type") not in ("choice", "short"):
                    if ex_obj.get("options") and len(ex_obj.get("options", [])) > 0:
                        ex_obj["type"] = "choice"
                    else:
                        ex_obj["type"] = "short"

                if not ex_obj.get("question"):
                    ex_obj["question"] = ex_obj.get("content", "题目暂缺")
                    ex_obj.pop("content", None)


                if ex_obj["type"] == "short":
                    ex_obj.pop("options", None)

                if ex_obj["type"] == "choice":
                    if not ex_obj.get("options"):
                        ex_obj["options"] = ["选项A", "选项B"]

                    answer_val = ex_obj.get("answer", "")
                    if answer_val and len(answer_val) == 1 and answer_val.isalpha():
                        idx = ord(answer_val.upper()) - ord('A')
                        if 0 <= idx < len(ex_obj["options"]):
                            ex_obj["answer"] = ex_obj["options"][idx]

                #包装 

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

