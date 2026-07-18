import requests
import time

BASE_URL = "http://127.0.0.1:8080"

tests = [
    {
        "name": "聊天接口 /api/chat",
        "url": f"{BASE_URL}/api/chat",
        "data": {"user_id": "u001", "message": "什么是操作系统"} 
    },
    {
        "name": "路径接口 /api/path",
        "url": f"{BASE_URL}/api/path",
        "data": {"user_id": "u001", "topic": "内存管理"}
    },
    {
        "name": "资源生成（未缓存） /api/resource/generate",
        "url": f"{BASE_URL}/api/resource/generate",
        "data": {"user_id": "u001", "topic": "死锁", "resource_type": "explanation"}  
    }
]

for test in tests:
    print(f"\n测试: {test['name']}")
    total_time = 0
    success_count = 0
    
    for i in range(10):
        try:
            start = time.time()
            resp = requests.post(test["url"], json=test["data"], timeout=30)
            elapsed = time.time() - start
            
            if resp.status_code == 200:
                total_time += elapsed
                success_count += 1
                print(f"  第 {i+1} 次: {elapsed:.2f}s")
            else:
                print(f"  第 {i+1} 次: 失败 (HTTP {resp.status_code}) - {resp.text[:200]}")
        except Exception as e:
            print(f"  第 {i+1} 次: 异常 ({e})")
    
    if success_count > 0:
        avg = total_time / success_count
        print(f"  ✅ 平均响应时间: {avg:.2f}s (成功 {success_count}/10)")
    else:
        print(f"  ❌ 全部失败")