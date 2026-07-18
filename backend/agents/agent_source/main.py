#输入参数转为字典传入
#主控函数，调用多agent,输出所需资源
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.agents.agent_source.animation_agent import agentanimation
from backend.agents.agent_source.code_agent import agentcode
from backend.agents.agent_source.exercise_agent import agentexercise
from backend.agents.agent_source.kn_agent import agentkn
from data.knowledge.KnowledgeBaseManager import KnowledgeBaseManager
from backend.agents.agent_source.lmm import SparkLLM
from backend.agents.agent_source.security_utils import filter_sensitive_fields
import json
import os, json, hashlib
from pathlib import Path
from json_repair import repair_json


# 知识库管理器
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  
KB_PATH = PROJECT_ROOT / "data" / "knowledge"
RESOURCE_CACHE_PATH = PROJECT_ROOT / "data" / "user_resources"
kb = KnowledgeBaseManager(str(KB_PATH))

llm=SparkLLM()

#输入参数示例
test_input={

    "user_id":"u001",
    "topic_id": "os_memory_04",
    "module":"存储器管理",
    "difficulty": "medium",
    "learning_style": "txt",
    "weak_points": ["页表映射"],
    "understanding": 0.6,
    "current_progress":"learning",
    "resource_type":["animation"]

}
# input_data=test_input



def get_profile_hash(input_data):
    # 提取关键画像字段，保证稳定
    profile = {
        "weak": sorted(input_data.get("weak_points", [])),
        "diff": input_data.get("difficulty", "medium"),
        "under": round(input_data.get("understanding", 0.5), 1)
    }
    return hashlib.md5(json.dumps(profile, sort_keys=True).encode()).hexdigest()

def get_cached_resource(user_id, topic_id, res_type, profile_hash):
    file_path = RESOURCE_CACHE_PATH / user_id / f"{topic_id}_{res_type}_{profile_hash}.json"
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_resource(user_id, topic_id, res_type, profile_hash, resource_obj):
    dir_path = RESOURCE_CACHE_PATH / user_id
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / f"{topic_id}_{res_type}_{profile_hash}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(resource_obj, f, ensure_ascii=False, indent=2)




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
    """
    校验输入参数的完整性与有效性
    """
    required_fields = [
        "user_id",
        "topic_id",
        "module",
        "resource_type"
    ]

    for field in required_fields:
        #检查字段是否存在
        if field not in data:
            raise ValueError(f"【资源生成agent】缺少必要字段: {field}")

        value = data[field]

        #检查字段值是否为 None
        if value is None:
            raise ValueError(f"【资源生成agent】字段 '{field}' 的值不能为 None")

        #如果是字符串类型，检查是否为空或仅包含空白字符
        if isinstance(value, str):
            if value.strip() == "":
                raise ValueError(f"【资源生成agent】字段 '{field}' 不能为空字符串")

        #针对 resource_type 的特殊校验：必须是非空列表，且元素有效
        if field == "resource_type":
            if not isinstance(value, list):
                raise ValueError(f"【资源生成agent】字段 'resource_type' 必须为列表类型，当前类型为 {type(value).__name__}")
            
            if len(value) == 0:
                raise ValueError(f"【资源生成agent】字段 'resource_type' 不能为空列表，请至少指定一种资源类型")
            
            #校验列表中的每个元素
            for idx, item in enumerate(value):
                if not isinstance(item, str):
                    raise ValueError(f"【资源生成agent】resource_type 列表中第 {idx+1} 个元素必须为字符串，当前为 {type(item).__name__}")
                if item.strip() == "":
                    raise ValueError(f"【资源生成agent】resource_type 列表中第 {idx+1} 个元素不能为空字符串")
                
def normalize_input(data):

    data.setdefault("learning_style", "txt")

    data.setdefault("weak_points", [])

    data.setdefault("understanding", 0.5)

    data.setdefault("current_progress", "learning")

    data.setdefault(
        "resource_type",
        ["mindmap"]
    )

    return data   
class agentCore:

    #需要从知识库传递一整个topic内容
    def run(self,input_data:dict):
        self.finaloutput = {}

        # 1. 参数标准化
        input_data = normalize_input(input_data)

        # 2. 参数校验
        validate_input(input_data)
        tasks=[]
        topic = kb.get_topic_by_id(input_data["topic_id"])

        if topic is None:
            print(f"【资源生成agent】错误：未找到知识点 {input_data['topic_id']}")
            return {"resources": []} 
        
                
        resource_types=input_data["resource_type"];
        if "animation" in resource_types:
            tasks.append(lambda: agentanimation().run(input_data, topic))

        if "code" in resource_types:
            tasks.append(lambda: agentcode().run(input_data, topic))

        if "exercise" in resource_types:
            tasks.append(lambda: agentexercise().run(input_data, topic))

        kn_types = ["explanation", "mindmap", "materials"]
        for rtype in kn_types:
            if rtype in resource_types:
                tasks.append(lambda r=rtype: agentkn().run(input_data, topic, [r]))


        # 并发执行所有任务
        with ThreadPoolExecutor(max_workers=5) as executor:
            # 提交所有任务，保存 future 对象
            future_to_task = {executor.submit(task): task for task in tasks}

            # 按完成顺序收集结果
            for future in as_completed(future_to_task):
                try:
                    result = future.result()
                    if result and isinstance(result, dict):
                        self.finaloutput.update(result)
                except Exception as e:
                    print(f"【资源生成agent】Agent 执行失败: {e}")

                    self.finaloutput[f"【资源生成agent】error_{str(e)}"] = {"error": str(e)}


        resources = []
        for key, resource_obj in self.finaloutput.items():
            if key == "error" or not isinstance(resource_obj, dict):
                continue
            resource_obj["subtype"] = key
            resources.append(resource_obj)

        return {"resources": resources}
# 返回json,最外层仅一个resources字段

def generate_resources(input_data: dict) -> dict:
    """
    统一的资源生成入口。
    输入必须包含：user_id, topic_id, module, resource_type
    返回：
        {"resources": [...]}
    """
    input_data = normalize_input(input_data)
    validate_input(input_data)

    user_id = input_data["user_id"]
    topic_id = input_data["topic_id"]
    profile_hash = get_profile_hash(input_data)
    requested_types = input_data["resource_type"]

    final_resources = []
    missing_types = []

    #检查缓存
    for res_type in requested_types:
        cached = get_cached_resource(user_id, topic_id, res_type, profile_hash)
        if cached is not None:
            final_resources.append(cached)
        else:
            missing_types.append(res_type)

    # 如果全部命中，过滤后返回
    if not missing_types:
        return {"resources": [filter_sensitive_fields(r) for r in final_resources]}

    #有缺失类型 ：生成缺失部分
    new_input = input_data.copy()
    new_input["resource_type"] = missing_types
    agent = agentCore()
    result = agent.run(new_input)

    #存储并合并（存储前和返回前都过滤）
    for res in result.get("resources", []):
        safe_res = filter_sensitive_fields(res)
        res_type = safe_res.get("subtype")
        if res_type:
            save_resource(user_id, topic_id, res_type, profile_hash, safe_res)
        final_resources.append(safe_res)

    return {"resources": final_resources}


# if __name__ == "__main__":
#     # 仅用于本地手动测试，不会影响正式导入
#     test_input = {
#         "user_id": "u001", 
#         "topic_id": "os_memory_06",
#         "module": "存储器管理",
#         "difficulty": "medium",
#         "resource_type": ["animation", "code_example", "exercise", "mindmap","explanation","materials"]
#     }
#     result = generate_resources(test_input)
#     print(json.dumps(result, ensure_ascii=False, indent=2))
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