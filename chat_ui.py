import streamlit as st
from openai import OpenAI
import re
import markdown
from io import BytesIO
from extractor import extract_meeting_info, extract_info

# ================== xhtml2pdf 导出 ==================
from xhtml2pdf import pisa

def markdown_to_pdf(markdown_text):
    """将 Markdown 文本转换为 PDF 字节流（使用 xhtml2pdf，完美中文支持）"""
    html = markdown.markdown(markdown_text)
    # 加入基础 CSS 和 UTF-8 声明
    html_full = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; }}
            h3 {{ color: #555; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    """
    pdf_bytes = BytesIO()
    # 使用 pisa 创建 PDF，encoding='utf-8' 确保中文正确显示
    pisa.CreatePDF(html_full, dest=pdf_bytes, encoding='utf-8')
    return pdf_bytes.getvalue()

# ================== 读取文档函数 ==================
def read_text_file(file):
    return file.read().decode("utf-8")

def read_docx_file(file):
    try:
        from docx import Document
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    except ImportError:
        st.error("python-docx 未安装，无法读取 .docx 文件。请运行: pip install python-docx")
        return None

def read_pdf_file(file):
    try:
        from pypdf import PdfReader
        reader = PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages])
    except ImportError:
        st.error("pypdf 未安装，无法读取 .pdf 文件。请运行: pip install pypdf")
        return None

def read_file_content(uploaded_file):
    if uploaded_file is None:
        return None
    file_type = uploaded_file.type
    if file_type == "text/plain":
        return read_text_file(uploaded_file)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return read_docx_file(uploaded_file)
    elif file_type == "application/pdf":
        return read_pdf_file(uploaded_file)
    else:
        st.error(f"不支持的文件类型: {file_type}")
        return None

# ================== 页面设置 ==================
st.set_page_config(page_title="AI 助手 & 会议纪要", layout="centered")
st.title("🤖 我的 AI 助手")

# ================== API Key 输入 ==================
api_key = st.text_input("DeepSeek API Key", type="password")
if not api_key:
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# ================== 聊天历史 ==================
if "messages" not in st.session_state:
    st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ================== 文件上传 ==================
uploaded_file = st.file_uploader(
    "📁 上传会议记录文件",
    type=["txt", "docx", "pdf"],
    help="支持 .txt, .docx, .pdf 格式"
)

file_content = ""
if uploaded_file is not None:
    file_content = read_file_content(uploaded_file)
    if file_content:
        st.success(f"✅ 已读取文件：{uploaded_file.name}，共 {len(file_content)} 个字符")
    else:
        st.error("❌ 读取文件失败")

# ================== 意图检测 ==================
def is_meeting_request(text):
    keywords = ["会议", "纪要", "整理", "记录", "讨论", "参会", "决议", "待办", "总结"]
    return any(kw in text for kw in keywords)

def extract_meeting_text(text):
    patterns = [
        r"整理(?:一下)?(?:会议)?(?:记录|纪要|文本)?[:：]?\s*(.+)",
        r"(?:帮我|请)(?:整理|总结)(?:一下)?(?:会议)?(?:记录|纪要)?[:：]?\s*(.+)",
        r"^(.+)(?:会议|纪要|讨论|记录|总结)(.+)$"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            content = match.group(1).strip()
            if len(content) >= 10:
                return content
    return text

# ================== 聊天输入 ==================
prompt = st.chat_input("说点什么... (例如：帮我整理会议记录：...)")

if prompt:
    if file_content and len(prompt) < 20:
        full_prompt = f"{prompt}\n\n以下是会议记录文件内容：\n{file_content}"
    else:
        full_prompt = prompt

    st.session_state.messages.append({"role": "user", "content": full_prompt})
    with st.chat_message("user"):
        st.markdown(full_prompt)

    if is_meeting_request(full_prompt):
        meeting_text = extract_meeting_text(full_prompt)
        if len(meeting_text) < 20:
            meeting_text = full_prompt

        with st.chat_message("assistant"):
            with st.spinner("🧠 正在生成会议纪要..."):
                try:
                    result = extract_meeting_info(meeting_text, api_key)

                    content = f"## 会议纪要：{result.get('topic', '无主题')}\n\n"
                    content += f"**日期：** {result.get('date', '未知')}\n"
                    content += f"**参会人员：** {', '.join(result.get('attendees', []))}\n\n"
                    content += f"### 摘要\n{result.get('summary', '无摘要')}\n\n"
                    content += "### 关键决议\n"
                    for res in result.get('resolutions', []):
                        content += f"- {res}\n"
                    if not result.get('resolutions'):
                        content += "- 暂无决议\n"
                    content += "\n### 待办事项\n"
                    for item in result.get('action_items', []):
                        content += f"- [ ] {item}\n"
                    if not result.get('action_items'):
                        content += "- 暂无待办事项\n"

                    st.markdown(content)
                    st.session_state.messages.append({"role": "assistant", "content": content})

                    # ===== PDF 导出按钮 =====
                    try:
                        pdf_bytes = markdown_to_pdf(content)
                        st.download_button(
                            label="📄 导出为 PDF",
                            data=pdf_bytes,
                            file_name="会议纪要.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.warning(f"PDF 导出遇到小问题，但你可以使用浏览器的 '打印 -> 保存为 PDF' 功能。错误信息：{e}")

                except Exception as e:
                    error_msg = f"生成会议纪要时出错：{str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    else:
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=st.session_state.messages,
                    stream=True
                )
                full_response = ""
                placeholder = st.empty()
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    file_content = ""