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
    
    SYSTEM_PASSWORD = st.secrets.get("APP_PASSWORD", None)
    SYSTEM_API_KEY = st.secrets.get("API_KEY", None)
    api_key = None
    
    user_password = st.text_input("🔑 访问密码", type="password", placeholder="输入密码，自动加载 Key")

    if SYSTEM_PASSWORD and user_password == SYSTEM_PASSWORD:
        api_key = SYSTEM_API_KEY
        st.success("✅ 密码正确！已加载令牌")
    else:
        if user_password: st.error("❌ 密码错误")
        st.caption("或者手动输入 API Key：")
        api_key = st.text_input("Key", type="password", label_visibility="collapsed")

    st.markdown("---")
    st.header("⚙️ API 设置")
    base_url = st.text_input("API 地址", value="https://hk-api.gptbest.vip/v1")
    st.caption("📝 文本模型 (DeepSeek)")
    text_model = st.text_input("Text Model", value="deepseek-chat", label_visibility="collapsed")
    st.caption("🖼️ 图片模型 (GPT-4o)")
    vision_model = st.text_input("Vision Model", value="gpt-4o-mini", label_visibility="collapsed")

# --- 🏗️ 功能标签页 ---
tab1, tab2 = st.tabs(["📝 文本生成提示词", "🖼️ 图片反推提示词 (看图)"])

# ==========================================
# 👉 标签 1：文本生成 (双语版)
# ==========================================
with tab1:
    st.subheader("✍️ 描述画面，生成 Prompt")
    user_input = st.text_area("你想画什么？", height=100, placeholder="例如：一只穿着宇航服的猫，赛博朋克风格...")

    c1, c2 = st.columns(2)
    with c1: ratio = st.selectbox("画幅", ["--ar 16:9", "--ar 9:16", "--ar 1:1", "--ar 3:4"])
    with c2: mode = st.selectbox("模式", ["标准模式 (MJ/SD)", "建筑设计", "自然语言 (Google)", "二次元 (Niji)", "写实摄影", "3D渲染"])

    # 🔥 核心修改：强制 AI 按格式输出双语
    base_instruction = """
    You are an expert AI prompt engineer.
    IMPORTANT: You must output the result in exactly two parts using the specific format below:
    
    CN: [Here write the optimized description in Chinese]
    EN: [Here write the final English prompt]
    
    Do not add any other text or explanations.
    """
    
    # 各模式的微调指令
    mode_rules = {
        "标准模式 (MJ/SD)": "For EN: Output comma-separated keywords. Focus on visual descriptors.",
        "建筑设计": "For EN: Target Architectural Visualization. Add tags: ArchDaily style, V-Ray, 8k.",
        "自然语言 (Google)": "For EN: Write a rich, descriptive English paragraph. Start with 'A photo of...'.",
        "二次元 (Niji)": "For EN: Anime style, cel shading, vibrant colors.",
        "写实摄影": "For EN: Photorealistic, 8k, shot on Sony A7RIV.",
        "3D渲染": "For EN: 3D render, blender, c4d, octane render."
    }
    
    sys_prompt = base_instruction + mode_rules.get(mode.split(" ")[0], "")

    if st.button("🚀 生成双语提示词", type="primary"):
        if not api_key: st.error("请先输入密码！"); st.stop()
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            with st.spinner('AI 正在双语构思...'):
                resp = client.chat.completions.create(
                    model=text_model,
                    messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_input}]
                )
                raw_content = resp.choices[0].message.content
