import streamlit as st
from openai import OpenAI
import base64

# 1. 页面设置
st.set_page_config(page_title="🎨 AI 提示词魔法师 Pro", page_icon="🪄", layout="centered")
st.title("✨ AI 提示词魔法师 Pro")

# --- 🛠️ 辅助函数 ---
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# --- 🔐 侧边栏：核心设置区 ---
with st.sidebar:
    st.header("🔐 身份验证")
    
    # 从云端保险箱读取配置
    SYSTEM_PASSWORD = st.secrets.get("APP_PASSWORD", None)
    SYSTEM_API_KEY = st.secrets.get("API_KEY", None)

    api_key = None
    
    # 1. 密码输入框
    user_password = st.text_input("🔑 访问密码", type="password", placeholder="输入密码，自动加载 Key")

    # 2. 验证逻辑
    if SYSTEM_PASSWORD and user_password == SYSTEM_PASSWORD:
        api_key = SYSTEM_API_KEY
        st.success("✅ 密码正确！已加载令牌")
    else:
        # 如果密码不对，显示手动输入框
        if user_password: st.error("❌ 密码错误")
        st.caption("或者手动输入 API Key：")
        api_key = st.text_input("Key", type="password", label_visibility="collapsed")

    st.markdown("---")
    st.header("⚙️ API 设置")
    
    # 👇 重点：这里默认值改成了你截图里的【香港路线】，记得加 /v1
    base_url = st.text_input("API 地址", value="https://hk-api.gptbest.vip/v1")
    
    st.caption("📝 文本模型 (DeepSeek)")
    text_model = st.text_input("Text Model", value="deepseek-chat", label_visibility="collapsed")
    
    st.caption("🖼️ 图片模型 (GPT-4o)")
    vision_model = st.text_input("Vision Model", value="gpt-4o-mini", label_visibility="collapsed")

# --- 🏗️ 功能标签页 ---
tab1, tab2 = st.tabs(["📝 文本生成提示词", "🖼️ 图片反推提示词 (看图)"])

# ==========================================
# 👉 标签 1：文本生成
# ==========================================
with tab1:
    st.subheader("✍️ 描述画面，生成 Prompt")
    user_input = st.text_area("你想画什么？", height=100, placeholder="例如：一座海边的白色美术馆，极简风格...")

    c1, c2 = st.columns(2)
    with c1: ratio = st.selectbox("画幅", ["--ar 16:9", "--ar 9:16", "--ar 1:1", "--ar 3:4"])
    with c2: mode = st.selectbox("模式", ["标准模式 (MJ/SD)", "建筑设计", "自然语言 (Google)", "二次元 (Niji)", "写实摄影", "3D渲染"])

    # 简化的系统提示词
    prompts_map = {
        "标准模式 (MJ/SD)": "Translate to English. Output comma-separated keywords. Visual descriptors.",
        "建筑设计": "Translate to English. Target: Architectural Visualization. Tags: ArchDaily style, V-Ray, 8k.",
        "自然语言 (Google)": "Translate to a rich, descriptive English paragraph. No tags. Start with 'A photo of...'.",
        "二次元 (Niji)": "Translate to English. Anime style, cel shading, vibrant colors.",
        "写实摄影": "Translate to English. Photorealistic, 8k, shot on Sony A7RIV.",
        "3D渲染": "Translate to English. 3D render, blender, c4d, octane render."
    }
    
    if st.button("🚀 生成文本提示词", type="primary"):
        if not api_key: st.error("请先输入密码！"); st.stop()
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            sys_prompt = prompts_map.get(mode.split(" ")[0], prompts_map["标准模式 (MJ/SD)"])
            
            with st.spinner('AI 正在构思...'):
                resp = client.chat.completions.create(
                    model=text_model,
                    messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_input}]
                )
                final = f"{resp.choices[0].message.content} {ratio}"
                
            st.code(final, language="text", wrap_lines=True)
        except Exception as e:
            st.error(f"出错：{e}")

# ==========================================
# 👉 标签 2：图片反推
# ==========================================
with tab2:
    st.subheader("🖼️ 上传图片，反推 Prompt")
    uploaded_file = st.file_uploader("拖入参考图", type=["jpg", "png"])
    
    if uploaded_file and st.button("🔍 开始反推"):
        if not api_key: st.error("请先输入密码！"); st.stop()
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            img_b64 = encode_image(uploaded_file)
            
            with st.spinner('AI 正在看图...'):
                resp = client.chat.completions.create(
                    model=vision_model,
                    messages=[{
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": "描述这张图的主体、风格、光影。输出英文关键词，逗号分隔。"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                        ]
                    }]
                )
            
            st.image(uploaded_file, width=200)
            st.code(resp.choices[0].message.content, language="text", wrap_lines=True)
        except Exception as e:
            st.error(f"出错：{e}")
