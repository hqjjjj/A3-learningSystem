import sys, json
sys.path.insert(0, '..')
from orchestrator.orchestrator import get_orchestrator

orch = get_orchestrator()
resource_input = {
    'topic_id': 'os_mem_02',
    'module': '内存管理-分页机制',
    'difficulty': 'medium',
    'learning_style': 'diagram',
    'weak_points': [],
    'understanding': 0.4,
    'current_progress': '分页基本概念',
    'resource_type': ['explanation', 'exercise']
}
result = orch._call_source_agent_raw(resource_input)
print(json.dumps(result, ensure_ascii=False, indent=2)[:1000])