#输入参数定义
from backend.agents.agent_source.prompts import build_prompt
from data.knowledge.KnowledgeBaseManager import KnowledgeBaseManager
from backend.agents.agent_source.lmm import SparkLLM
import json
import os

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
    learning_goal: str
    difficulty: str
    learning_style:str
    weak_points: list
    understanding:float
    #是否为复习
    current_progress:str
#输入参数示例
test_input={
    "topic_id": "os_mem_04",
    "learning_goal": "理解页表结构",
    "module":"内存管理-分页机制",
    "difficulty": "medium",
    "learning_style": "visual",
    "weak_points": ["页表映射"],
    "understanding": 0.6,
    "current_progress":"learning"
  

}

input_data=test_input


import json5

def parse_output(result):
    result = result.strip()
    # 去除 markdown 代码块
    if result.startswith("```json"):
        result = result[7:]
    if result.startswith("```"):
        result = result[3:]
    if result.endswith("```"):
        result = result[:-3]
    result = result.strip()
    try:
        # 优先用 json5 解析
        return json5.loads(result)
    except Exception as e:
        print(f"json5 解析也失败: {e}")
        print(f"原始内容前200字符: {result[:200]}")
        return {"content": result, "error": str(e)}
    
    
class agentCore:
    # system和user 双层结构
    #需要从知识库传递一整个topic内容
    def run(self,input_data):
        # get_module是否正确存疑
        topic = kb.get_topic_by_id(input_data["topic_id"])
        system, user = build_prompt(input_data, topic)
        result = llm.generate(system, user)
        return parse_output(result)

agent=agentCore()
result=agent.run(input_data)
print(result)