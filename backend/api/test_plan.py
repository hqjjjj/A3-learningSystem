import sys, json
sys.path.insert(0, '..')
from orchestrator.orchestrator import get_orchestrator

orch = get_orchestrator()
profile = {
    'user_id': 'test_001',
    'major': '计算机', 'grade': '大三', 'course': '操作系统',
    'knowledge_level': {'分页基本概念': 0.4},
    'progress': {'current_topic': '分页基本概念'},
    'difficulty': 'medium', 'learning_style': 'diagram',
    'weak_points': [], 'resource_type': ['explanation'],
    'cognitive_style': {'visual': 0.7, 'textual': 0.15, 'auditory': 0.15}
}
result = orch._call_plan_agent('test_001', profile)
print(json.dumps(result, ensure_ascii=False, indent=2))