# api/api_finish.py
from fastapi import APIRouter
from pydantic import BaseModel
from orchestrator.orchestrator import finish_view_resource

router = APIRouter()

class FinishViewRequest(BaseModel):
    user_id: str
    resource_id: str
    duration: int

@router.post("/finish_view")
def finish_view(req: FinishViewRequest):
    result = finish_view_resource(
        user_id=req.user_id,
        resource_id=req.resource_id,
        duration=req.duration
    )
    return {"status": "success", "data": result}