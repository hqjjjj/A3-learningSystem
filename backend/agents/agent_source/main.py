#输入参数定义
from backend.agents.agent_source.code_agent import agentcode
from backend.agents.agent_source.exercise_agent import agentexercise
from backend.agents.agent_source.kn_agent import agentkn
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
# class agentInput:
#     input_data = {
#     "topic_id": source_data.get("topic_id"),
#     "module": source_data.get("module"),
#     "difficulty": source_data.get("difficulty"),
#     "learning_style": source_data.get("learning_style"),
#     "weak_points": source_data.get("weak_points", []),
#     "understanding": source_data.get("understanding", 0.5),
#     "current_progress": source_data.get("current_progress", "learning"),
#     "resource_type": source_data.get("resource_type", [])
#     }

#输入参数示例
test_input={
    "topic_id": "os_mem_04",
    "module":"内存管理-分页机制",
    "difficulty": "medium",
    "learning_style": "diagram",
    "weak_points": ["页表映射"],
    "understanding": 0.6,
    "current_progress":"learning",
    "resource_type":["mindmap","exercise","materials","code_example"]

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
    def __init__(self):
        self.finaloutput = {}
    # system和user 双层结构
    #需要从知识库传递一整个topic内容
    def run(self,input_data):
        topic = kb.get_topic_by_id(input_data["topic_id"])
        if "code_example" in input_data["resource_type"]:
            code=agentcode()
            self.finaloutput.update(code.run(input_data,topic))
        if"exercise"in input_data["resource_type"]:
            exercise=agentexercise()
            self.finaloutput.update(exercise.run(input_data,topic))
        if "explanation" in input_data["resource_type"] or "mindmap" in input_data["resource_type"] or "materials" in input_data["resource_type"]:
            kn=agentkn()
            self.finaloutput.update(kn.run(input_data,topic,input_data["resource_type"]))
        return self.finaloutput






agent=agentCore()
result=agent.run(input_data)
print(result)