import streamlit as st
import requests
import json

# ============================================================
# 【核心配置：请在此处填入你的信息】
# ============================================================
# 1. 填入你截图中的 API Key (XPmU...开头的那串)
MY_REAL_API_KEY = "gTBJ6GhqKOimfYGhys1gbAlzxbwsOoy3"

# 2. 填入你的 智能体ID/助手ID (即 b2bcff... 那串)
MY_ASSISTANT_ID = "2035992077834375936"

# 3. 核心接口地址 (根据文档通常为以下地址)
MY_API_URL = "https://yuanqi.tencent.com/openapi/v1/agent/chat/completions"
# ============================================================

st.set_page_config(page_title="一到五队专利合规审查系统", layout="wide")
st.title("🛡️ 一到五队专利许可合同智能合规审查平台")
st.markdown("---")

# 侧边栏
st.sidebar.header("配置选项")
user_input_key = st.sidebar.text_input("临时 API Key (可选)", type="password")

# 主界面
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 合同输入")
    user_identity = st.selectbox("你的身份", ["甲方（许可方）", "乙方（被许可方）"])
    contract_text = st.text_area("请粘贴专利许可合同文本", height=500, placeholder="在此处粘贴专利合同文本...")
    submit_btn = st.button("开始深度审查")

if submit_btn:
    final_api_key = user_input_key if user_input_key else MY_REAL_API_KEY

    if not final_api_key or "你的真实" in final_api_key:
        st.error("❌ 请先在代码中填入正确的 API Key")
    elif not contract_text:
        st.warning("⚠️ 请输入合同内容")
    else:
        with st.spinner("正在调用腾讯元器进行合规审查..."):
            try:
                # 1. 严格按照文档定义的 URL
                url = 'https://yuanqi.tencent.com/openapi/v1/agent/chat/completions'

                # 2. 严格按照文档定义的请求头 (增加了 X-Source)
                headers = {
                    'X-Source': 'openapi',
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {final_api_key}'
                }

                # 3. 严格按照文档定义的请求体结构
                data = {
                    "assistant_id": MY_ASSISTANT_ID,  # 对应文档中的 appid
                    "user_id": "tester_zhang",  # 对应文档中的 username，必填
                    "stream": False,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"身份：{user_identity}\n请审查以下合同：\n\n{contract_text}"
                                }
                            ]
                        }
                    ]
                }

                # 发送请求
                response = requests.post(url, headers=headers, json=data)

                if response.status_code != 200:
                    st.error(f"调用失败 (状态码: {response.status_code})")
                    st.json(response.json())  # 如果报错，这里会显示具体的错误原因
                else:
                    res_json = response.json()
                    with col2:
                        st.subheader("📊 审查报告")
                        # 4. 按照文档返回参数路径提取内容
                        # choices[0] -> message -> content
                        try:
                            report_content = res_json['choices'][0]['message']['content']
                            st.markdown(report_content)

                            st.download_button(
                                label="下载报告 (Markdown)",
                                data=report_content,
                                file_name="patent_review_report.md"
                            )
                        except (KeyError, IndexError):
                            st.warning("解析内容失败，原始返回如下：")
                            st.json(res_json)

            except Exception as e:
                st.error(f"程序运行异常: {e}")
st.markdown("---")
st.caption("注：本系统由得理法律大数据提供底层支持。")