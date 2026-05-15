# logger.py
from pathlib import Path
from models import BehaviorEvent
import json
from threading import Lock
# 测试数据，数据由总控传入
# event = BehaviorEvent(
#     user_id="u001",
#     event_type="submit_answer",
#     topic="页表",
#     correct_rate=0.3,
#     time=datetime.now()
# )

file_lock=Lock()

Behavior_Path=Path("data/users_events")

def  log_event(event:BehaviorEvent):
    with file_lock:
        Behavior_Path.mkdir(parents=True, exist_ok=True)

        user_file = Behavior_Path / f"{event.user_id}.json"
            
        try:
            with open(user_file, "r", encoding="utf-8") as f:
                # 读取：加载并解析为python对象list[dict{}]
                data=json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = [] 


        #追加新型,Pydantic 模型转换为字典，并确保类型可 JSON 序列化,把该字典添加到列表末尾
        data.append(event.model_dump(mode="json"))

        # 写回
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False, indent=2)


    
