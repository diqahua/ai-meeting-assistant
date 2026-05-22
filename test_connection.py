from openai import OpenAI

# 请务必替换成你自己的 API Key！
client = OpenAI(
    api_key="sk-7b7a361d99fe40e889c656ef21e8427a",  # 这里替换成你的 sk-xxx
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "你好，请用一句话介绍一下你自己。"}
    ]
)

print("DeepSeek 回复：", response.choices[0].message.content)