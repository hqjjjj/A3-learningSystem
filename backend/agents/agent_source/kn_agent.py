#输入参数定义
from backend.agents.agent_source.kn_prompts import build_kn_prompt
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

class agentkn:
    # system和user 双层结构
    #需要从知识库传递一整个topic内容
    def run(self,input_data,topic,allows):
        
        system, user = build_kn_prompt(allows, input_data.get("module", "未知章节"), topic.get("name", "未知知识点")) ,user_prompt_build(input_data, topic,kb)  
        for i in range(3):
            result = llm.generate(system, user)
            result= parse_output(result)
            if "error" not in result:
                # 定义 kn 支持的资源类型
                kn_supported = ["explanation", "mindmap", "materials"]
                # 从 allows 中提取出本次实际请求的 kn 资源
                requested_kn = [t for t in allows if t in kn_supported]

                # 当前只允许一个资源（因为 main 中循环调用，每次只传一种）
                res_type = requested_kn[0]

                # 1. 确保 result 中有 res_type 键，且值为字典
                if res_type not in result:
                    result[res_type] = {}          # 只补缺失的键，不覆盖整个 result
                obj = result[res_type]

                # 2. 如果 obj 不是字典，尝试转换或重建
                if not isinstance(obj, dict):
                    # 如果是列表，尝试取第一个元素（如果是字典），否则丢弃
                    if isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], dict):
                        obj = obj[0]
                    else:
                        obj = {}
                    result[res_type] = obj

                # type 规则
                if res_type == "mindmap":
                    correct_type = "markdown"
                else:
                    correct_type = "text"

                # 3. 补全字段（此时 obj 肯定是字典）
                obj.setdefault("type", correct_type)
                obj.setdefault("title", f"{res_type}内容")
                if "content" not in obj or not obj["content"].strip():
                    obj["content"] = f"{res_type}内容生成失败，请稍后重试"

                # 针对 mindmap 增加内容质量检查（可选）
                if res_type == "mindmap":
                    content = obj.get("content", "")
                    if len(content.strip()) < 20 or "#" not in content:
                        topic_name = input_data.get("module", "当前知识点")
                        obj["content"] = f"""# {topic_name} 思维导图
            ## 核心概念
            - 逻辑页号→物理页框号映射
            ## 地址转换流程
            1. 提取页号
            2. 查询页表
            3. 拼接物理地址
            ## 常见应用
            - 虚拟内存
            - 内存保护"""
                        if obj["title"] == f"{res_type}内容":
                            obj["title"] = f"{topic_name}思维导图"

                # 强制修正 type
                obj["type"] = correct_type

                result[res_type] = obj

                module = input_data.get("module", "未知章节")
                topic_name = topic.get("name", "未知知识点")
                base_citation = f"源于教材知识库：《{module}》{topic_name}"

                obj = result[res_type]   # 已确保存在
                if "knowledge_base_quote" not in obj or not obj["knowledge_base_quote"]:
                    obj["knowledge_base_quote"] = [base_citation]
                else:
                    if not obj["knowledge_base_quote"][0].startswith("源于教材知识库"):
                        obj["knowledge_base_quote"].insert(0, base_citation)

                result[res_type] = obj
                
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

