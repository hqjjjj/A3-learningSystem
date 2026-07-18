
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.agent_source.main import generate_resources
import time
import json

# ============================================================
# 测试配置
# ============================================================

def run_test(name, resource_types):
    print(f"\n▶ 测试: {name}")
    print(f"   资源类型: {resource_types}")
    
    input_data = {
        "user_id": "u007",
        "topic_id": "os_file_03",  # 文件操作
        "module": "文件管理",
        "resource_type": resource_types,
        "difficulty": "medium"
    }
    
    start = time.time()
    try:
        result = generate_resources(input_data)
        elapsed = time.time() - start
        
        # 统计生成的资源数量
        resources = result.get("resources", [])
        print(f"   ✅ 成功，耗时: {elapsed:.2f} 秒")
        print(f"   📄 生成资源数: {len(resources)}")
        for r in resources:
            print(f"      - {r.get('subtype', 'unknown')}")
        return {"name": name, "count": len(resource_types), "time": elapsed, "success": True}
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return {"name": name, "count": len(resource_types), "time": None, "success": False}


# ============================================================
# 执行测试（先清理缓存，确保首次生成）
# ============================================================
print("=" * 60)
print("资源生成并发调度测试（直接调用函数）")
print("验证 agentCore 的 ThreadPoolExecutor 并发效果")
print("=" * 60)
print("\n⚠️ 注意：本次测试会生成真实资源，建议先清理缓存")
print("   如需清理，删除 data/user_resources/u007/ 目录")

# 先清理缓存（可选）
# import shutil
# cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'user_resources', 'u007')
# if os.path.exists(cache_dir):
#     shutil.rmtree(cache_dir)
#     print("✅ 已清理缓存")
# print()

# ============================================================
# 执行测试
# ============================================================
results = []

# 测试1: 1种资源
results.append(run_test("1种资源", ["explanation"]))

# 测试2: 3种资源
results.append(run_test("3种资源", ["explanation", "mindmap", "exercise"]))

# 测试3: 5种资源
results.append(run_test("5种资源", ["explanation", "mindmap", "exercise", "code_example", "materials"]))

# ============================================================
# 结果分析
# ============================================================
print("\n" + "=" * 60)
print("测试结果汇总")
print("=" * 60)

success_results = [r for r in results if r["success"]]

if len(success_results) >= 2:
    # 找基准（1种资源的耗时）
    base = None
    for r in success_results:
        if r["count"] == 1:
            base = r
            break
    
    if base:
        print(f"\n基准耗时 (1种资源): {base['time']:.2f} 秒")
        print("\n| 测试场景 | 资源数量 | 总耗时 | 与基准比值 | 并发效果 |")
        print("|----------|----------|--------|------------|----------|")
        
        for r in success_results:
            ratio = r["time"] / base["time"] if base["time"] else 0
            if r["count"] == 1:
                effect = "基准"
            elif ratio < 1.5:
                effect = "✅ 优秀 (并发有效)"
            elif ratio < 2.0:
                effect = "⚠️ 一般"
            else:
                effect = "❌ 较差"
            print(f"| {r['name']} | {r['count']}种 | {r['time']:.2f}s | {ratio:.2f}x | {effect} |")
        
        # 结论
        print("\n" + "=" * 60)
        print("结论")
        print("=" * 60)
        
        five_result = None
        for r in success_results:
            if r["count"] == 5:
                five_result = r
                break
        
        if five_result:
            ratio_5 = five_result["time"] / base["time"] if base["time"] else 0
            if ratio_5 < 1.5:
                print(f"✅ 5种资源生成总耗时 ({five_result['time']:.2f}s) 是单种资源 ({base['time']:.2f}s) 的 {ratio_5:.2f} 倍")
                print("✅ 小于 1.5 倍，agentCore 并发调度有效！")
            else:
                print(f"⚠️ 5种资源生成总耗时 ({five_result['time']:.2f}s) 是单种资源 ({base['time']:.2f}s) 的 {ratio_5:.2f} 倍")
                print("⚠️ 大于 1.5 倍，可能受限于 LLM API 速率限制")
        else:
            print("⚠️ 未找到5种资源的测试结果")
    else:
        print("⚠️ 未找到1种资源的测试结果")
else:
    print("⚠️ 测试数据不足，请检查是否有测试失败")