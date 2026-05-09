#输入参数定义
from prompts import build_prompt
from data.knowledge.KnowledgeBaseManager import KnowledgeBaseManager
kb=KnowledgeBaseManager()
# 111
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

class agentCore:
    # system和user 双层结构
    #需要从知识库传递一整个topic内容
    def run(input_data):
        # get_module是否正确存疑
        module_data=kb.get_module(input_data["module"])
        topic=kb.get_topic_by_id(
        module_data,
        input_data["topic_id"]
        )
        message=build_prompt(
        input_data,
        topic
        )
        result=llm.generate(message)
        return parse_output(result)


