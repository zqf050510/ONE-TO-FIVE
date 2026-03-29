import streamlit as st
import requests
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
import PyPDF2
import io
import json

# ============================================================
# 【核心配置】
# ============================================================
MY_REAL_API_KEY = "gTBJ6GhqKOimfYGhys1gbAlzxbwsOoy3"
MY_ASSISTANT_ID = "2035992077834375936"
MY_API_URL = "https://yuanqi.tencent.com/openapi/v1/agent/chat/completions"


# ============================================================
# 【工具函数：文件解析与生成】
# ============================================================
def extract_text_from_docx(file):
    """从 Word 文档中提取文字"""
    try:
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        st.error(f"Word解析失败: {e}")
        return ""


def extract_text_from_pdf(file):
    """从 PDF 文档中提取文字"""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            content = page.extract_text()
            if content:
                text += content
        return text
    except Exception as e:
        st.error(f"PDF解析失败: {e}")
        return ""


def generate_docx(report_text):
    """
    将 AI 生成的报告内容转换为专业 Word 文档
    设置字体为：仿宋，字号为：小四
    """
    doc = Document()

    # 1. 设置文档全局默认样式（可选，但更稳妥）
    style = doc.styles['Normal']
    font = style.font
    font.name = '仿宋'
    font.size = Pt(12)  # 小四对应的点数是 12
    # 核心：设置东亚字符集为仿宋，确保中文生效
    font._element.rPr.rFonts.set(qn('w:eastAsia'), '仿宋')

    # 2. 添加标题（标题单独设置）
    heading = doc.add_heading('一到五队 - 专利合规审查报告', 0)
    # 如果想把标题也改成仿宋，需要单独对 run 进行操作
    for run in heading.runs:
        run.font.name = '仿宋'
        run.font.size = Pt(16)  # 二号或三号字
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '仿宋')
        run.font.bold = True

    # 3. 将文本按行写入 Word，并对每一行应用字体和字号
    for line in report_text.split('\n'):
        if line.strip():
            p = doc.add_paragraph()
            run = p.add_run(line.strip())

            # --- 核心修改：设置字体和字号 ---
            run.font.name = '仿宋'
            # 必须设置东亚字符集，否则中文会变成默认的新宋体
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '仿宋')
            # 设置字号为 Pt(12)，对应中文“小四”
            run.font.size = Pt(12)

    # 将文档保存到内存流中
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


# ============================================================
# 【界面设置】
# ============================================================
st.set_page_config(page_title="一到五队专利合规审查系统", layout="wide", page_icon="🛡️")

# 初始化 Session State
if 'contract_content' not in st.session_state:
    st.session_state['contract_content'] = ""
if 'last_file_name' not in st.session_state:
    st.session_state['last_file_name'] = ""

st.title("🛡️ 一到五队专利许可合同智能合规审查平台")
st.markdown("---")

# 侧边栏：配置与功能按钮
st.sidebar.header("配置与工具")
user_input_key = st.sidebar.text_input("临时 API Key (可选)", type="password")

if st.sidebar.button("🗑️ 一键清空所有内容"):
    st.session_state['contract_content'] = ""
    st.session_state['last_file_name'] = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("💡 提示：支持上传 PDF/Word 或直接粘贴文本进行审查。")

# 主界面布局
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 合同输入")

    # 1. 身份界定
    user_identity = st.selectbox(
        "您的身份角色",
        ["甲方（许可方）", "乙方（被许可方）", "侵权纠纷原告", "侵权纠纷被告"]
    )

    # 2. 文件上传功能
    uploaded_file = st.file_uploader("直接上传合同文件 (支持 PDF, DOCX)", type=['docx', 'pdf'])

    if uploaded_file is not None and uploaded_file.name != st.session_state['last_file_name']:
        with st.spinner("正在解析文件内容..."):
            parsed_text = ""
            if uploaded_file.name.endswith('.docx'):
                parsed_text = extract_text_from_docx(uploaded_file)
            elif uploaded_file.name.endswith('.pdf'):
                parsed_text = extract_text_from_pdf(uploaded_file)

            if parsed_text:
                st.session_state['contract_content'] = parsed_text
                st.session_state['last_file_name'] = uploaded_file.name
                st.rerun()

    contract_text = st.text_area(
        "合同文本内容",
        value=st.session_state['contract_content'],
        height=450,
        placeholder="在此处粘贴文本，或通过上方按钮上传文件...",
    )

    st.session_state['contract_content'] = contract_text
    submit_btn = st.button("🚀 开始深度合规审查")

# 逻辑处理
if submit_btn:
    final_api_key = user_input_key if user_input_key else MY_REAL_API_KEY

    if not final_api_key or len(final_api_key) < 10:
        st.error("❌ 请检查 API Key 配置（请在侧边栏填入 Key）")
    elif not st.session_state['contract_content'].strip():
        st.warning("⚠️ 请输入或上传合同内容")
    else:
        with st.spinner("🔍 正在检索专利法条并进行深度分析..."):
            try:
                headers = {
                    'X-Source': 'openapi',
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {final_api_key}'
                }

                prompt_text = f"""
                作为资深专利律师，请针对以下身份和合同进行深度审查。
                用户身份：{user_identity}

                审查重点必须包含：
                1. 专利范围分析与授权合法性
                2. 许可费条款的公平性与合理性
                3. 专利有效期限判断与技术使用范围校验
                4. 针对该身份的潜在法律风险识别
                5. 具体的修改建议并引用相关法律依据

                待审查合同内容如下：
                {st.session_state['contract_content']}
                """

                data = {
                    "assistant_id": MY_ASSISTANT_ID,
                    "user_id": "researcher_zhang",
                    "stream": False,
                    "messages": [
                        {"role": "user", "content": [{"type": "text", "text": prompt_text}]}
                    ]
                }

                response = requests.post(MY_API_URL, headers=headers, json=data)

                if response.status_code != 200:
                    st.error(f"调用失败 (状态码: {response.status_code})")
                else:
                    res_json = response.json()
                    with col2:
                        st.subheader("📊 审查报告")
                        try:
                            report_content = res_json['choices'][0]['message']['content']
                            st.markdown(report_content)

                            # --- 核心修改：生成并下载 Word 格式报告 (仿宋，小四) ---
                            docx_file = generate_docx(report_content)

                            st.download_button(
                                label="📥 下载专业审查报告 (Word 格式)",
                                data=docx_file,
                                file_name="专利合规审查报告.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                        except (KeyError, IndexError):
                            st.warning("解析内容失败，原始返回如下：")
                            st.json(res_json)

            except Exception as e:
                st.error(f"程序运行异常: {e}")

st.markdown("---")
st.caption("注：本系统由一到五队基于腾讯元器及得理法律大数据提供技术支持。")
