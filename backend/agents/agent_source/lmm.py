from openai import OpenAI

class SparkLLM:
    def __init__(self):
        self.client = OpenAI(
            api_key="sk-ws-H.EDDMREL.BYsw.MEYCIQDKftr9UEUcLCamIm3BIjl5jNFDyG8c1pfCNf3bWfgkpwIhAI3U6AFl3ZGu14diTmHfXsPQAuNTImUr98h-Wx7dJFQ8",  # 换成你实际用的密钥
            base_url="https://ws-hr5a678q05zwljxu.cn-beijing.maas.aliyuncs.com/compatible-mode/v1", 
        )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model="qwen-plus",  
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=False,
            temperature=0.7,
            max_tokens=32768,
        )
        return response.choices[0].message.content