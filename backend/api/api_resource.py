from fastapi import APIRouter
from pydantic import BaseModel

from orchestrator.orchestrator import (
    generate_single_resource,
    finish_view_resource,
    submit_answer_result
)

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
        "result":result
    }


# 用户使用完资源
class FinishViewRequest(BaseModel):
        user_id: str
        resource_type: str
        topic:str
        duration: int
@router.post("/finish_view")
def finish_view(req: FinishViewRequest):

    result = finish_view_resource(
        user_id=req.user_id,
        resource_type=req.resource_type,
        duration=req.duration,
        topic=req.topic
    )

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