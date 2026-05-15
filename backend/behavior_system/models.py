# models.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BehaviorEvent(BaseModel):
    user_id: str


    # 事件类型决定对象有哪些参数：
    # 如果是对话，对象为
    # user_id：巴拉巴拉
    # event_type：“   ”
    # time：0
    # message：巴拉巴拉
    
    # 如果是做题，对象为
    # user_id：巴拉巴拉
    # time：。。。
    # topic：。。。
    # resource_type："exercise"
    # correct_rate:..(做题特有)
    # duration：。。。
    event_type: str


    # 访问时长
    time: datetime


    # 当前知识点
    topic: Optional[str] = None


    # 当前访问的资源
    resource_type: Optional[str] = None


    # 如果event_type为exercise，获取做题正确率
    correct_rate: Optional[float] = None


    # 单位：秒
    duration: Optional[int] = None

    #用户输入到对话框的提问，直接传给用户画像agent即可
    message:Optional[str]=None
