#输入参数定义
from backend.agents.agent_source.code_prompt import system_prompt_code
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
    return system_prompt_code, user_prompt_build(user_input, topic,kb)   
class agentcode:
    # system和user 双层结构
    #需要从知识库传递一整个topic内容
    def run(self,input_data,topic):
        
        system, user = build_prompt(input_data, topic,kb)
        for i in range(3):
            result = llm.generate(system, user)
            result= parse_output(result)
            if "error" not in result:
                return result
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

