#输入参数定义
from backend.agents.agent_source.prompts import build_prompt
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
class agentInput:
    topic_id:str
    module:str
    difficulty: str
    learning_style:str
    weak_points: list
    understanding:float
    #是否为复习
    current_progress:str
    resource_type:list
#输入参数示例
test_input={
    "topic_id": "os_mem_04",
    "module":"内存管理-分页机制",
    "difficulty": "medium",
    "learning_style": "visual",
    "weak_points": ["页表映射"],
    "understanding": 0.6,
    "current_progress":"learning",
    "resource_type":["explanation","mindmap","exercise","materials","code_example"]

}

input_data=test_input


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
    
class agentCore:
    # system和user 双层结构
    #需要从知识库传递一整个topic内容
    def run(self,input_data):
        topic = kb.get_topic_by_id(input_data["topic_id"])
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

agent=agentCore()
result=agent.run(input_data)
print(result)