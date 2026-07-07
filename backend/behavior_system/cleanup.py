# backend/behavior_system/cleanup.py
import json
from pathlib import Path

BEHAVIOR_PATH = Path("data/users_events")
MAX_EVENTS = 500  # 修正了变量名拼写错误 (原为 MAX_EVETS)

def clean_user_events(user_id: str):
    """清洗用户行为记录，保留最近 MAX_EVENTS 条"""
    user_file = BEHAVIOR_PATH / f"{user_id}.json"
    try:
        with open(user_file, "r", encoding="utf-8") as f:
            # 读取：加载并解析为python对象list[dict{}]
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = [] 
    
    if len(data) > MAX_EVENTS:
        # 只保留最近 500 条
        data = data[-MAX_EVENTS:]

        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

# =======================================================
# 🔥 新增：总控对接专用入口
# 这样 orchestrator 里的 from cleanup import cleanup_events 就能完美工作了
# =======================================================
def cleanup_events(user_id: str):
    """总控调用的兼容接口"""
    clean_user_events(user_id)