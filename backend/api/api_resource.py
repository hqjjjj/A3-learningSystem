#D:\软件杯\UserModelingAgent\backend\api\api_resource.py
from fastapi import APIRouter
from pydantic import BaseModel

from orchestrator.orchestrator import (
    generate_single_resource,
    finish_view_resource,
    submit_answer_result
)
from backend.agents.agent_source.main import generate_resources

router = APIRouter()

# 用户申请资源
class ResourceRequest(BaseModel):
    user_id:str
    topic:str
    resource_type:str

@router.post("/generate")
def generate(rr:ResourceRequest):
    result=generate_single_resource(
        user_id=rr.user_id,
        topic=rr.topic,
        resource_type=rr.resource_type
    )
    return {
    "status": "success",
    "data": result
    }


# 用户使用完资源
class FinishViewRequest(BaseModel):
        user_id: str
        resource_type: str
        topic:str
        duration: int
@router.post("/finish_view")
def finish_view(req: FinishViewRequest):
    # 1. 先调用总控层完成行为记录和画像更新
    result = finish_view_resource(
        user_id=req.user_id,
        resource_id=req.resource_type,
        duration=req.duration,
        topic=req.topic  
    )
    
    # 👇 2. 关键修复：将 user_id 手动补进返回数据中 (针对总控里调用 generate_resources 时的缺失)
    # 因为总控层在返回资源时，有时候不会把 user_id 保留在 output 中。
    # 我们在 API 层做个补丁。
    if "data" in result and result["data"] is not None:
        if isinstance(result["data"], dict) and "user_id" not in result["data"]:
            result["data"]["user_id"] = req.user_id

    return {
        "status": "success",
        "data": result
    }

# 用户提交题目
class SubmitAnswerRequest(BaseModel):
     user_id:str
     topic:str
     correct_rate:float
     duration:int

@router.post("/submit_answer")
def submit_answer(req: SubmitAnswerRequest):

    result = submit_answer_result(
        user_id=req.user_id,
        topic=req.topic,
        correct_rate=req.correct_rate,
        duration=req.duration
    )

    return {
        "status": "success",
        "data": result
    }

# 使用新封装的资源生成函数
class GenerateResourcesRequest(BaseModel):
    user_id: str
    topic_id: str
    module: str
    resource_type: list
    difficulty: str = None
    weak_points: list = None
    understanding: float = None
    learning_style: str = None
    current_progress: str = None

@router.post("/generate_resources")
def generate_resources_api(req: GenerateResourcesRequest):
    # 构建输入数据
    input_data = {
        "topic_id": req.topic_id,
        "module": req.module,
        "resource_type": req.resource_type,
    }
    
    # 添加可选参数
    if req.difficulty:
        input_data["difficulty"] = req.difficulty
    if req.weak_points:
        input_data["weak_points"] = req.weak_points
    if req.understanding:
        input_data["understanding"] = req.understanding
    if req.learning_style:
        input_data["learning_style"] = req.learning_style
    if req.current_progress:
        input_data["current_progress"] = req.current_progress
    
    # 调用资源生成函数
    result = generate_resources(input_data)
    
    return {
        "status": "success",
        "data": result
    }