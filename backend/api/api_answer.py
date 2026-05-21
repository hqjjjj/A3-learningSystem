# api/api_answer.py
from fastapi import APIRouter
from pydantic import BaseModel
from orchestrator.orchestrator import submit_answer_result

router = APIRouter()

class SubmitAnswerRequest(BaseModel):
    user_id: str
    topic: str
    correct_rate: float
    duration: int

@router.post("/submit")
def submit_answer(req: SubmitAnswerRequest):
    result = submit_answer_result(
        user_id=req.user_id,
        topic=req.topic,
        correct_rate=req.correct_rate,
        duration=req.duration
    )
    return {"status": "success", "data": result}