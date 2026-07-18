import requests
import time

BASE_URL = "http://127.0.0.1:8080"


test_data = {
    "user_id": "u007", 
    "topic": "文件操作",   
    "resource_type": "explanation"  
}

url = f"{BASE_URL}/api/resource/generate"

print("=" * 50)
print("缓存效果测试")
print("=" * 50)

# ----- 第一次请求（未命中缓存，走 LLM）-----
print(f"\n[1/2] 第一次请求 (预期：未命中缓存，调用LLM)")
start = time.time()
resp1 = requests.post(url, json=test_data, timeout=60)
time1 = time.time() - start

if resp1.status_code == 200:
    print(f"  ✅ 成功，耗时: {time1:.2f} 秒")
    # 打印一下返回内容的简要信息，确认是真实资源
    data1 = resp1.json()
    if "data" in data1 and "generated_resource" in data1["data"]:
        title = data1["data"]["generated_resource"].get("title", "无标题")
        print(f"  📄 资源标题: {title}")
else:
    print(f"  ❌ 失败 (HTTP {resp1.status_code})")

# 等待1秒，避免干扰
time.sleep(1)

# ----- 第二次请求（应该命中缓存）-----
print(f"\n[2/2] 第二次请求 (预期：命中缓存，直接读文件)")
start = time.time()
resp2 = requests.post(url, json=test_data, timeout=10)
time2 = time.time() - start

if resp2.status_code == 200:
    print(f"  ✅ 成功，耗时: {time2:.3f} 秒 (注意单位是毫秒级)")
    data2 = resp2.json()
    if "data" in data2 and "generated_resource" in data2["data"]:
        title = data2["data"]["generated_resource"].get("title", "无标题")
        print(f"  📄 资源标题: {title}")
        
        # 检查两次返回的内容是否一致
        if resp1.text == resp2.text:
            print("\n  ✅ 两次返回的资源内容完全一致（缓存有效）")
        else:
            print("\n  ⚠️ 两次返回内容不一致（可能缓存未生效或ID不同）")
else:
    print(f"  ❌ 失败 (HTTP {resp2.status_code})")

# 结论
print("\n" + "=" * 50)
print("测试结论")
print("=" * 50)
print(f"第一次耗时: {time1:.2f} 秒")
print(f"第二次耗时: {time2:.3f} 秒")

if time2 < 0.1:
    print("✅ 第二次耗时 < 100ms，缓存机制生效！")
elif time2 < time1:
    print("✅ 第二次比第一次快，缓存机制有效，但响应稍慢（可能包含网络/序列化开销）")
else:
    print("⚠️ 第二次不比第一次快，可能未命中缓存（请检查 topic 是否一致或清理过缓存）")