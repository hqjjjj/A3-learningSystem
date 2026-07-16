# backend/behavior_system/logger.py
from pathlib import Path
from models import BehaviorEvent
import json
from threading import Lock
from datetime import datetime  # 补充导入 datetime

# 测试数据，数据由总控传入
# event = BehaviorEvent(
#     user_id="u001",
#     event_type="submit_answer",
#     topic="页表",
#     correct_rate=0.3,
#     time=datetime.now()
# )

file_lock = Lock()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
Behavior_Path = BASE_DIR / "data" / "users_events"

def log_event(event: BehaviorEvent):
    """Pydantic 模型标准记录函数"""
    with file_lock:
        Behavior_Path.mkdir(parents=True, exist_ok=True)

        user_file = Behavior_Path / f"{event.user_id}.json"
            
        try:
            with open(user_file, "r", encoding="utf-8") as f:
                # 读取：加载并解析为python对象list[dict{}]
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = [] 

        # 追加新型, Pydantic 模型转换为字典，并确保类型可 JSON 序列化
        data.append(event.model_dump(mode="json"))

        # 写回
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 打印日志
        print(f"【行为系统】已记录用户 {event.user_id} 的行为事件：{event.event_type}（当前共 {len(data)} 条）")

# =======================================================
# 🔥 新增：总控对接专用入口
# 这样 orchestrator 里的 from logger import log_behavior 就能完美工作了
# =======================================================
def log_behavior(user_id: str, action: str, **kwargs):
    """
    兼容总控 (Orchestrator) 调用的包装函数。
    将常规参数自动转换为 BehaviorEvent 模型。
    """
        # ===== 过滤：查看资源时长小于 10 秒则不记录 =====
    if action == "view_resource":
        duration = kwargs.get("duration")
        if duration is not None and duration < 10:
            print(f" [行为系统Logger] 忽略时长 {duration}s 的浏览记录（小于10秒）")
            return
    # ================================================
    # 构造符合 BehaviorEvent 模型的参数字典
    event_data = {
        "user_id": user_id,
        "event_type": action,  # 注意：这里将总控传的 action 映射为 event_type
        "time": datetime.now()
    }
    
    # 将剩余的参数（如 correct_rate, message, duration 等）合并进去
    event_data.update(kwargs)
    
    # 实例化 Pydantic 模型
    try:
        event = BehaviorEvent(**event_data)
        # 调用你原本写好的逻辑进行保存
        log_event(event)
    except Exception as e:
        print(f"⚠️ [Logger] 行为记录失败: {e}")
# =======================================================