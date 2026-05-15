# analyze.py
import json
from collections import Counter
from pathlib import Path

ANALYZE_SIZE=100

BEHAVIOR_PATH = Path("data/users_events")

def analyze_behavior(user_id: str):

    user_file=BEHAVIOR_PATH/f"{user_id}.json"

    try:
        with open(user_file, "r", encoding="utf-8") as f:
            user_events = json.load(f)
            if len(user_events)>ANALYZE_SIZE:
                user_events=user_events[-ANALYZE_SIZE:]
    except(FileNotFoundError, json.JSONDecodeError):
    # 找不到文件或文件为空就返回字典
        return {}


    # 1. 正确率分析

    topic_scores={}
    for e in user_events:
        topic=e.get("topic")
        correct_rate=e.get("correct_rate")

        if topic and correct_rate is not None:
            if topic  not in topic_scores:
                topic_scores[topic]=[]
            topic_scores[topic].append(correct_rate)

    knowledge_level={}
    
    for topic,scores in topic_scores.items():
        knowledge_level[topic]=max(
                0,
                 min(
                round(sum(scores)/len(scores),2),
                1
             )
                )


    # 2. 资源偏好分析

    resource_type=[]
    resources=[
        e["resource_type"]
        for e in user_events
        if e.get("resource_type")
    ]
    resource_type=[
        item[0]
        for item in Counter(resources).most_common(3)
    ]
    # 3. 学习节奏分析


    durations = [
        e["duration"]
        for e in user_events
        if e.get("duration")
    ]

    learning_pace = "normal"

    if durations:
        avg_duration = sum(durations) / len(durations)

        if avg_duration < 60:
            learning_pace = "fast"

        elif avg_duration > 1200:
            learning_pace = "slow"
        else:
            learning_pace = "normal"

    return {
        "knowledge_level": knowledge_level,
        "resource_type": resource_type,
        "learning_pace": learning_pace
    }