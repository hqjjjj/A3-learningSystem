#输入参数转为字典传入
#主控函数，调用多agent,输出所需资源
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

# #输入参数示例
# test_input={
#     "topic_id": "os_mem_04",
#     "module":"内存管理-分页机制",
#     "difficulty": "medium",
#     "learning_style": "txt",
#     "weak_points": ["页表映射"],
#     "understanding": 0.6,
#     "current_progress":"learning",
#     "resource_type":["explanation","mindmap","exercise","materials","code_example"]

# }
# input_data=test_input


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
def validate_input(data):

    required_fields = [
        "topic_id",
        "module",
        "difficulty",
        "resource_type"
    ]

    for field in required_fields:

        if field not in data:

            raise ValueError(
                f"缺少必要字段: {field}"
            )
def normalize_input(data):

    data.setdefault("learning_style", "txt")

    data.setdefault("weak_points", [])

    data.setdefault("understanding", 0.5)

    data.setdefault("current_progress", "learning")

    data.setdefault(
        "resource_type",
        ["explanation"]
    )

    return data   
class agentCore:

    # system和user 双层结构
    #需要从知识库传递一整个topic内容
    def run(self,input_data:dict):
        self.finaloutput = {}

        # 1. 参数标准化
        input_data = normalize_input(input_data)

        # 2. 参数校验
        validate_input(input_data)

        topic = kb.get_topic_by_id(input_data["topic_id"])
        
        if "code_example" in input_data["resource_type"]:
            code=agentcode()
            self.finaloutput.update(code.run(input_data,topic))
        if"exercise"in input_data["resource_type"]:
            exercise=agentexercise()
            self.finaloutput.update(exercise.run(input_data,topic))
        
        kn_types = ["explanation", "mindmap", "materials"]

        for rtype in kn_types:

            # 只处理用户真正请求的资源
            if rtype in input_data["resource_type"]:

                kn = agentkn()

                result = kn.run(
                    input_data,
                    topic,
                    [rtype]   # 这里只传一个资源类型
                )

                self.finaloutput.update(result)
        # 格式化输出
        resources = []
        for key, resource_obj in self.finaloutput.items():
            if key == "error" or not isinstance(resource_obj, dict):
                continue
            resource_obj["subtype"] = key
            resources.append(resource_obj)

        return {"resources": resources}
# 返回json,最外层仅一个resources字段


agent=agentCore()
# result=agent.run(input_data)
# print(result)

# 调用提示
# data.resources.forEach(res => {
#   switch(res.type) {
#     case "code": renderCode(res); break;
#     case "choice": renderExercise(res); break;
#     case "markdown": renderMarkdown(res); break;
#     case "text": 
#       if (res.subtype === "explanation") renderExplanation(res);
#       else if (res.subtype === "materials") renderMaterials(res);
#       break;
#   }
# });