from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BehaviorEvent(BaseModel):
    user_id: str

    event_type: str

    time: datetime

    topic: Optional[str] = None

    resource_type: Optional[str] = None

    correct_rate: Optional[float] = None
    # 单位：秒
    duration: Optional[int] = None

    is_completed: Optional[bool] = None
