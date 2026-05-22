import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import os
import webbrowser
from extractor import extract_meeting_info, extract_info


# ================== 工具函数 ==================
def read_input_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None


def save_meeting_minutes(data, output_path):
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


def save_general_info(data, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 信息提取结果\n\n")
        f.write("## 日期\n")
        for d in data.get('dates', []): f.write(f"- {d}\n")
        f.write("\n## 地点\n")
        for loc in data.get('locations', []): f.write(f"- {loc}\n")
        f.write("\n## 人物\n")
        for p in data.get('people', []): f.write(f"- {p}\n")
        f.write("\n## 关键词\n")
        for k in data.get('keywords', []): f.write(f"- {k}\n")


def copy_to_clipboard(content):
    root.clipboard_clear()
    root.clipboard_append(content)
    root.update()


# ================== 处理核心（新增 API Key 参数） ==================
def process_file(input_path, output_dir, mode, api_key, status_text):
    status_text.insert(tk.END, "📖 正在读取文件...\n")
    status_text.see(tk.END)

    text = read_input_file(input_path)
    if text is None:
        status_text.insert(tk.END, "❌ 错误：找不到文件，请检查路径。\n")
        return None, None

    status_text.insert(tk.END, f"🤖 正在调用 AI （模式：{mode}）...\n")
    status_text.see(tk.END)

    try:
        if mode == "会议纪要":
            result = extract_meeting_info(text, api_key)
            base_name = os.path.splitext(os.path.basename(input_path))[0] + "_会议纪要.md"
            output_path = os.path.join(output_dir, base_name)
            save_meeting_minutes(result, output_path)
            content = f"# 会议纪要：{result.get('topic', '无主题')}\n\n"
            content += f"日期：{result.get('date', '未知')}\n"
            content += f"参会人员：{', '.join(result.get('attendees', []))}\n\n"
            content += f"摘要：{result.get('summary', '无摘要')}\n\n"
            content += "关键决议：\n"
            for res in result.get('resolutions', []):
                content += f"- {res}\n"
            content += "\n待办事项：\n"
            for item in result.get('action_items', []):
                content += f"- [ ] {item}\n"
        else:  # 通用提取
            result = extract_info(text, api_key)
            base_name = os.path.splitext(os.path.basename(input_path))[0] + "_提取结果.md"
            output_path = os.path.join(output_dir, base_name)
            save_general_info(result, output_path)
            content = f"# 信息提取结果\n\n"
            content += f"日期：{', '.join(result.get('dates', []))}\n"
            content += f"地点：{', '.join(result.get('locations', []))}\n"
            content += f"人物：{', '.join(result.get('people', []))}\n"
            content += f"关键词：{', '.join(result.get('keywords', []))}\n"

        status_text.insert(tk.END, f"✅ 完成！文件已保存至：\n{output_path}\n")
        status_text.see(tk.END)
        return output_path, content
    except Exception as e:
        status_text.insert(tk.END, f"❌ 处理出错：{str(e)}\n")
        status_text.see(tk.END)
        return None, None


def start_processing():
    api_key = api_key_entry.get().strip()
    if not api_key:
        messagebox.showwarning("提示", "请先输入 DeepSeek API Key")
        return

    input_path = input_entry.get()
    if not input_path:
        messagebox.showwarning("提示", "请先选择输入文件")
        return

    output_dir = output_dir_entry.get() or os.path.dirname(input_path)
    if not os.path.exists(output_dir):
        messagebox.showerror("错误", "输出目录不存在，请重新选择")
        return

    mode = mode_var.get()

    # 清空状态栏
    status_text.delete(1.0, tk.END)
    status_text.insert(tk.END, f"🔑 API Key：{api_key[:8]}...\n")
    status_text.insert(tk.END, f"📁 输入文件：{input_path}\n")
    status_text.insert(tk.END, f"📄 输出目录：{output_dir}\n")
    status_text.insert(tk.END, f"⚙️ 模式：{mode}\n")

    # 禁用按钮
    btn_run.config(state=tk.DISABLED)
    btn_open_folder.config(state=tk.DISABLED)
    btn_copy.config(state=tk.DISABLED)

    def process_thread():
        output_path, content = process_file(input_path, output_dir, mode, api_key, status_text)
        if output_path:
            btn_open_folder.config(state=tk.NORMAL, command=lambda: webbrowser.open(os.path.dirname(output_path)))
            btn_copy.config(state=tk.NORMAL, command=lambda: copy_to_clipboard(content))
            global last_output_path
            last_output_path = output_path
        else:
            btn_open_folder.config(state=tk.DISABLED)
            btn_copy.config(state=tk.DISABLED)
        btn_run.config(state=tk.NORMAL)

    thread = threading.Thread(target=process_thread)
    thread.daemon = True
    thread.start()


def select_file():
    filename = filedialog.askopenfilename(
        title="选择输入文件",
        filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
    )
    if filename:
        input_entry.delete(0, tk.END)
        input_entry.insert(0, filename)
        if not output_dir_entry.get():
            output_dir_entry.delete(0, tk.END)
            output_dir_entry.insert(0, os.path.dirname(filename))


def select_output_dir():
    directory = filedialog.askdirectory(title="选择输出目录")
    if directory:
        output_dir_entry.delete(0, tk.END)
        output_dir_entry.insert(0, directory)


# ================== 创建界面 ==================
root = tk.Tk()
root.title("🤖 智能会议纪要生成器 (API Key 版)")
root.geometry("700x650")
root.resizable(True, True)

# 变量
mode_var = tk.StringVar(value="会议纪要")
last_output_path = None

# --- 新增：API Key 输入区域 ---
frame_key = tk.Frame(root, pady=5)
frame_key.pack(fill="x", padx=20)

tk.Label(frame_key, text="DeepSeek API Key：", font=("Arial", 11)).pack(side="left")
api_key_entry = tk.Entry(frame_key, width=50, font=("Arial", 10), show="*")  # show="*" 会隐藏字符
api_key_entry.pack(side="left", padx=5)
tk.Label(frame_key, text="(去 platform.deepseek.com 申请)", font=("Arial", 9), fg="gray").pack(side="left")

# --- 输入文件 ---
frame_input = tk.Frame(root, pady=5)
frame_input.pack(fill="x", padx=20)

tk.Label(frame_input, text="输入文件：", font=("Arial", 11)).pack(side="left")
input_entry = tk.Entry(frame_input, width=50, font=("Arial", 10))
input_entry.pack(side="left", padx=5)
tk.Button(frame_input, text="📂 浏览", command=select_file, bg="#e1e1e1").pack(side="left")

# --- 输出目录 ---
frame_output = tk.Frame(root, pady=5)
frame_output.pack(fill="x", padx=20)

tk.Label(frame_output, text="输出目录：", font=("Arial", 11)).pack(side="left")
output_dir_entry = tk.Entry(frame_output, width=50, font=("Arial", 10))
output_dir_entry.pack(side="left", padx=5)
tk.Button(frame_output, text="📁 选择", command=select_output_dir, bg="#e1e1e1").pack(side="left")

# --- 模式切换 ---
frame_mode = tk.Frame(root, pady=5)
frame_mode.pack(fill="x", padx=20)

tk.Label(frame_mode, text="处理模式：", font=("Arial", 11)).pack(side="left")
tk.Radiobutton(frame_mode, text="会议纪要", variable=mode_var, value="会议纪要").pack(side="left", padx=10)
tk.Radiobutton(frame_mode, text="通用信息提取", variable=mode_var, value="通用提取").pack(side="left", padx=10)

# --- 运行按钮 ---
frame_btn = tk.Frame(root, pady=10)
frame_btn.pack()

btn_run = tk.Button(frame_btn, text="🚀 生成并保存", command=start_processing,
                    bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), padx=20, pady=5)
btn_run.pack(side="left", padx=5)

btn_open_folder = tk.Button(frame_btn, text="📂 打开输出文件夹", state=tk.DISABLED,
                            font=("Arial", 10), padx=10)
btn_open_folder.pack(side="left", padx=5)

btn_copy = tk.Button(frame_btn, text="📋 复制内容", state=tk.DISABLED,
                     font=("Arial", 10), padx=10)
btn_copy.pack(side="left", padx=5)

# --- 状态输出 ---
frame_status = tk.Frame(root, pady=10)
frame_status.pack(fill="both", expand=True, padx=20)

tk.Label(frame_status, text="运行状态：", font=("Arial", 10)).pack(anchor="w")
status_text = scrolledtext.ScrolledText(frame_status, height=15, font=("Consolas", 10))
status_text.pack(fill="both", expand=True)

# 启动
if __name__ == "__main__":
    root.mainloop()