import requests
import json
import hashlib
import hmac
import base64
import datetime
from urllib.parse import urlencode

# 你的凭证
API_KEY = "6e31903de32ff6578f5d5e5e137d5328"
API_SECRET = "MDgyODNjMTg1MzdjZGM5YTU4NDlmYWNh"

HOST = "spark-api-open.xf-yun.com"
PATH = "/v1/chat/completions"
REQUEST_URL = f"https://{HOST}{PATH}"

def create_url():
    now = datetime.datetime.now(datetime.timezone.utc)
    date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
    signature_origin = f"host: {HOST}\ndate: {date}\nPOST {PATH} HTTP/1.1"
    signature_sha = hmac.new(
        API_SECRET.encode('utf-8'),
        signature_origin.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    signature = base64.b64encode(signature_sha).decode('utf-8')
    authorization_origin = f'api_key="{API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
    q = {"authorization": authorization, "date": date, "host": HOST}
    return f"{REQUEST_URL}?{urlencode(q)}"

print("步骤1: 测试基础网络...")
try:
    test_resp = requests.get("https://www.baidu.com", timeout=5)
    print(f"  -> 百度访问正常，状态码: {test_resp.status_code}")
except Exception as e:
    print(f"  -> ❌ 百度访问失败: {e}")

print("\n步骤2: 测试星火API（禁用代理，超时30秒）...")
try:
    url = create_url()
    resp = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json={
            "model": "generalv3.5",
            "messages": [
                {"role": "user", "content": "回复：测试成功"}
            ],
            "max_tokens": 10
        },
        timeout=30,
        proxies={"http": None, "https": None}  # 关键：禁用系统代理
    )
    print(f"  -> 状态码: {resp.status_code}")
    print(f"  -> 返回内容: {resp.text[:200]}")
except Exception as e:
    print(f"  -> ❌ 请求异常: {e}")