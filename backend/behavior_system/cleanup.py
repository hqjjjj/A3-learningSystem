# cleanup.py
import json
from pathlib import Path

BEHAVIOR_PATH = Path("data/users_events")

MAX_EVETS=500

def clean_user_events(user_id:str):
    user_file=BEHAVIOR_PATH / f"{user_id}.json"
    try:
        with open(user_file, "r", encoding="utf-8") as f:
                # 读取：加载并解析为python对象list[dict{}]
            data=json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
            data = [] 
    
    if len(data)>MAX_EVETS:
         data=data[-MAX_EVETS:]

         with open(user_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)