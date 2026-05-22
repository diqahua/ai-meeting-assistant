import json
from openai import OpenAI


def extract_info(text, api_key):
    """通用信息提取（需要传入 API Key）"""
    if not api_key:
        raise ValueError("sk-e720332948f04305a6297f204a41b159")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

    prompt = f"""
    你是一个信息提取助手。请从以下文本中提取：
    - 日期（格式：YYYY-MM-DD）
    - 地点
    - 人物
    - 关键词（3-5个）

    输出纯JSON：
    {{"dates": [], "locations": [], "people": [], "keywords": []}}

    文本：
    {text}
    """
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    content = response.choices[0].message.content
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    return json.loads(content)


def extract_meeting_info(text, api_key):
    """会议纪要专用提取（需要传入 API Key）"""
    if not api_key:
        raise ValueError("API Key 不能为空")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

    prompt = f"""
    你是一个专业的会议纪要助手。请根据以下会议记录文本，生成一份结构化的会议纪要。

    需提取的信息：
    1. 会议主题（根据内容自行拟定）
    2. 会议日期
    3. 参会人员
    4. 会议摘要（2-3句话概括核心内容）
    5. 关键决议（列出大家达成的共识）
    6. 待办事项（列表，每条格式为：任务内容 - 负责人）

    输出格式：纯 JSON，不要任何解释。
    示例：
    {{
        "topic": "AI技术交流会复盘",
        "date": "2026-05-22",
        "attendees": ["张三", "李四"],
        "summary": "会议讨论了AI技术交流会的进展和成果...",
        "resolutions": ["项目进入下一阶段", "每周同步一次进度"],
        "action_items": ["整理参会名单 - 王五", "输出会议纪要 - 张三"]
    }}

    以下是会议记录文本：
    {text}
    """
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    content = response.choices[0].message.content
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    return json.loads(content)