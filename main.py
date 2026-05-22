import sys
import json
from extractor import extract_meeting_info, extract_info


def read_input_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ 找不到文件：{file_path}")
        return None


def save_meeting_minutes(data, output_path):
    """专门为会议纪要设计的美化输出"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# 会议纪要：{data.get('topic', '无主题')}\n\n")
        f.write("## 基本信息\n")
        f.write(f"- **日期：** {data.get('date', '未知')}\n")
        f.write(f"- **参会人员：** {', '.join(data.get('attendees', []))}\n\n")

        f.write("## 摘要\n")
        f.write(f"{data.get('summary', '无摘要')}\n\n")

        f.write("## 关键决议\n")
        for res in data.get('resolutions', []):
            f.write(f"- {res}\n")
        if not data.get('resolutions'):
            f.write("- 暂无决议\n")

        f.write("\n## 待办事项\n")
        for item in data.get('action_items', []):
            f.write(f"- [ ] {item}\n")
        if not data.get('action_items'):
            f.write("- 暂无待办事项\n")
    print(f"✅ 会议纪要已保存至：{output_path}")


def run_agent(instruction, input_file="input.txt", output_file="output.md"):
    print(f"🤖 收到指令：{instruction}")

    # 指令识别与路由
    if "会议" in instruction or "纪要" in instruction:
        text = read_input_file(input_file)
        if text is None:
            return "❌ 没有输入文件，请确保 input.txt 存在并包含会议记录"

        print("📝 正在提取会议信息...")
        result = extract_meeting_info(text)
        save_meeting_minutes(result, output_file)
        return f"✅ 完成！已生成高质量的会议纪要：{output_file}"
    else:
        return f"🤔 我还不理解这个指令：{instruction}，试试 '整理会议纪要'"


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "agent":
        instruction = sys.argv[2] if len(sys.argv) > 2 else "整理会议纪要"
        result = run_agent(instruction)
        print(result)
    else:
        # 普通模式：保持旧逻辑，提取基本信息
        print("🔧 普通模式运行中...")
        text = read_input_file("input.txt")
        if text:
            result = extract_info(text)
            print("提取结果：", json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("请先创建 input.txt 文件")


if __name__ == "__main__":
    main()