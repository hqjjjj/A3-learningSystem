from openai import OpenAI

class SparkLLM:
    def __init__(self):
        self.client = OpenAI(
            api_key="OALNHAzMNPceyqfkinMN:iahJPnpBnZEBAxAzsBNq",  
            base_url="https://spark-api-open.xf-yun.com/agent/v1/",
        )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model="spark-x",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=False,
            temperature=0.7,
            max_tokens=4096,
        )
        return response.choices[0].message.content