import requests
import json

# 获取知识图谱
response = requests.get("http://localhost:8080/graph")
data = response.json()

print("=" * 60)
print("知识图谱节点")
print("=" * 60)

# 打印每个节点
for node in data["nodes"]:
    print(f"\n【{node['id']}】{node['name']}")
    print(f"  难度: {node['difficulty']}")
    print(f"  前置依赖: {node['prerequisites']}")
    print(f"  后续知识点: {node['dependents']}")

print("\n" + "=" * 60)
print("依赖关系边")
print("=" * 60)

# 打印边
for edge in data["edges"]:
    source = edge['source']
    target = edge['target']
    source_name = next((n['name'] for n in data['nodes'] if n['id'] == source), source)
    target_name = next((n['name'] for n in data['nodes'] if n['id'] == target), target)
    print(f"  {source_name} → {target_name}")