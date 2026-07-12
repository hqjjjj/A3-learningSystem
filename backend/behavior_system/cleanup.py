# backend/behavior_system/cleanup.py
import json
from pathlib import Path
from typing import List, Dict, Any
import asyncio
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BEHAVIOR_PATH = BASE_DIR / "data" / "users_events"
MAX_EVENTS = 500
CLEANUP_THRESHOLD = 600  # 超过这个值才清理

def clean_user_events(user_id: str) -> None:
    """清洗用户行为记录，保留最近 MAX_EVENTS 条"""
    user_file = BEHAVIOR_PATH / f"{user_id}.json"
    try:
        with open(user_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = [] 
    
    if len(data) > MAX_EVENTS:
        data = data[-MAX_EVENTS:]
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

async def add_user_event_async(user_id: str, event: Dict[str, Any]) -> None:
    """异步添加用户行为记录，并在添加后自动清理"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, add_user_event, user_id, event)

def add_user_event(user_id: str, event: Dict[str, Any]) -> None:
    """添加用户行为记录，并在添加后自动清理"""
    user_file = BEHAVIOR_PATH / f"{user_id}.json"
    
    # 读取现有数据
    try:
        with open(user_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    
    # 添加时间戳
    event['timestamp'] = datetime.now().isoformat()
    
    # 添加新事件
    data.append(event)
    
    # 只在超过阈值时才清理
    if len(data) > CLEANUP_THRESHOLD:
        clean_user_events(user_id)
        return
    
    # 写入文件
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def cleanup_events(user_id: str) -> None:
    """总控调用的兼容接口"""
    clean_user_events(user_id)

def cleanup_all_users() -> None:
    """清理所有用户的行为记录"""
    if not BEHAVIOR_PATH.exists():
        return
        
    for user_file in BEHAVIOR_PATH.glob("*.json"):
        user_id = user_file.stem
        clean_user_events(user_id)
