import requests
import json
import hashlib
import hmac
import base64
import datetime
from urllib.parse import urlencode

# 你的凭证（已经正确，不用改了）
APP_ID = "820d31b7"
API_KEY = "6e31903de32ff6578f5d5e5e137d5328"      # 保持你刚才已经填好的
API_SECRET = "MDgyODNjMTg1MzdjZGM5YTU4NDlmYWNh" # 保持你刚才已经填好的

HOST = "spark-api-open.xf-yun.com"
PATH = "/v1/chat/completions"
REQUEST_URL = "https://" + HOST + PATH

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
    query_params = {
        "authorization": authorization,
        "date": date,
        "host": HOST
    }
    return f"{REQUEST_URL}?{urlencode(query_params)}"

def test_spark(prompt):
    """测试星火API，并自动解析出干净的JSON"""
    url = create_url()
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "model": "generalv3.5",
        "messages": [
            {"role": "system", "content": "你是一个学习画像分析助手。请严格按照JSON格式输出，不要加任何说明文字，不要用markdown代码块包裹，直接输出纯JSON。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "max_tokens": 512         # 在这里加长，防止截断
    }
    
    print("正在发送请求...")
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    result = resp.json()
    
    print("HTTP状态码:", resp.status_code)
    
    if result.get("code") == 0:
        content = result["choices"][0]["message"]["content"]
        
        # 清理可能包裹的 markdown 代码块标记
        content = content.strip()
        if content.startswith("```"):
            content = content.split('\n', 1)[1]  # 去掉第一行 ```json
            if content.endswith("```"):
                content = content.rsplit('\n', 1)[0]  # 去掉最后一行 ```
        
        print("✅ 调用成功！提取结果：")
        parsed = json.loads(content)
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
        return parsed
    else:
        print("❌ 调用失败，完整返回：")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return None

if __name__ == "__main__":
    test_prompt = """
    学生说："我计算机专业大三，这学期学操作系统，内存分页那部分完全不会。"
    请从这句话提取：专业、课程、薄弱知识点，用JSON格式输出。
    """
    test_spark(test_prompt)