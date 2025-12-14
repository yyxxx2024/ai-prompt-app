import streamlit as st
from openai import OpenAI
import base64

# 1. 页面设置
st.set_page_config(page_title="🎨 AI 提示词魔法师 Pro", page_icon="🪄", layout="centered")
st.title("✨ AI 提示词魔法师 Pro")

# --- 🛠️ 辅助函数 ---
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# --- 🔐 身份验证逻辑 (升级版：使用 session_state 缓存) ---
# 初始化全局 Key，防止刷新丢失
if "cached_api_key" not in st.session_state:
    st.session_state.cached_api_key = None

with st.sidebar:
    st.header("🔐 身份验证")
    
    # 获取云端配置
    SYSTEM_PASSWORD = st.secrets.get("APP_PASSWORD", None)
    SYSTEM_API_KEY = st.secrets.get("API_KEY", None)
    
    user_password = st.text_input("🔑 访问密码", type="password", placeholder="输入密码，自动加载 Key")
    
    # 手动 Key 输入框
    manual_key = st.text_input("或手动输入 Key", type="password", label_visibility="collapsed")

    # 🔄 验证逻辑核心
    if SYSTEM_PASSWORD and user_password == SYSTEM_PASSWORD:
        # 如果密码对，且云端有 Key，就存入缓存
        if SYSTEM_API_KEY:
            st.session_state.cached_api_key = SYSTEM_API_KEY
            st.success("✅ 密码正确！令牌已锁定")
        else:
            st.error("⚠️ 密码正确，但云端未配置 API_KEY！请检查 Secrets。")
    elif manual_key:
        # 如果填了手动 Key，存入缓存
        st.session_state.cached_api_key = manual_key
    elif user_password and user_password != SYSTEM_PASSWORD:
        st.error("❌ 密码错误")

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
# 👉 标签 1：文本生成 (双语 + 高级选项)
# ==========================================
with tab1:
    st.subheader("✍️ 描述画面，生成 Prompt")
    user_input = st.text_area("你想画什么？", height=100, placeholder="例如：一个Aecom设计的超高层建筑...")

    c1, c2 = st.columns(2)
    with c1: 
        ratio = st.selectbox("画幅", ["--ar 16:9", "--ar 9:16", "--ar 1:1", "--ar 3:4", "--ar 4:3"])
    with c2: 
        mode = st.selectbox("模式", ["建筑设计", "标准模式 (MJ/SD)", "自然语言 (Google)", "二次元 (Niji)", "写实摄影", "3D渲染"])

    # ✨ 高级选项
    with st.expander("🎨 点击展开：高级选项 (光线、视角、材质)"):
        col_a, col_b, col_c = st.columns(3)
        with col_a: 
            lighting = st.selectbox("💡 光线氛围", ["不指定", "自然光 (Natural)", "电影级布光 (Cinematic)", "黄金时刻 (Golden Hour)", "赛博霓虹 (Neon)", "柔和光 (Soft)", "戏剧性光影 (Dramatic)"])
        with col_b: 
            camera = st.selectbox("📷 镜头视角", ["不指定", "广角 (Wide Angle)", "微距 (Macro)", "鸟瞰 (Aerial)", "人视角度 (Eye Level)", "鱼眼 (Fisheye)", "正视图 (Front View)"])
        with col_c: 
            material = st.selectbox("🧶 材质/渲染", ["不指定", "虚幻引擎5 (UE5)", "V-Ray渲染", "磨砂质感 (Matte)", "金属光泽 (Metallic)", "胶片颗粒 (Film Grain)", "水彩 (Watercolor)"])
        negative_prompt = st.text_input("🚫 负面提示词", value="text, watermark, blurry, low quality, bad anatomy, ugly")

    # 🔥 核心指令
    base_instruction = """
    You are an expert AI prompt engineer.
    IMPORTANT: You must output the result in exactly two parts using the specific format below:
    CN: [Here write the optimized description in Chinese]
    EN: [Here write the final English prompt]
    Do not add any other text or explanations.
    """
    
    mode_rules = {
        "标准模式 (MJ/SD)": "For EN: Output comma-separated keywords. Visual descriptors.",
        "建筑设计": "For EN: Target Architectural Visualization. Add tags: ArchDaily style, V-Ray, 8k, hyper-realistic.",
        "自然语言 (Google)": "For EN: Write a rich, descriptive English paragraph. Start with 'A photo of...'.",
        "二次元 (Niji)": "For EN: Anime style, cel shading, vibrant colors.",
        "写实摄影": "For EN: Photorealistic, 8k, shot on Sony A7RIV.",
        "3D渲染": "For EN: 3D render, blender, c4d, octane render."
    }
    
    sys_prompt = base_instruction + mode_rules.get(mode.split(" ")[0], "")

    if st.button("🚀 生成双语提示词", type="primary"):
        # 👉 这里改用了 session_state 来检查 Key，非常稳定
        current_key = st.session_state.cached_api_key
        
        if not current_key:
            st.error("🚨 无法获取 API Key！")
            st.warning("原因可能是：\n1. 还没输入密码。\n2. 密码正确但云端 secrets 里的 API_KEY 是空的。")
            st.stop()
        
        try:
            client = OpenAI(api_key=current_key, base_url=base_url)
            
            details = []
            if lighting != "不指定": details.append(f"光线: {lighting}")
            if camera != "不指定": details.append(f"视角: {camera}")
            if material != "不指定": details.append(f"材质: {material}")
            
            full_req = f"用户描述: {user_input}。 额外要求: {', '.join(details)}"

            with st.spinner('AI 正在双语构思...'):
                resp = client.chat.completions.create(
                    model=text_model,
                    messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": full_req}]
                )
                
                raw_content = resp.choices[0].message.content
                
                cn_text = "解析中..."
                en_text = raw_content
                
                if "CN:" in raw_content and "EN:" in raw_content:
                    parts = raw_content.split("EN:")
                    cn_text = parts[0].replace("CN:", "").strip()
                    en_text = parts[1].strip()
                
                final_en = f"{en_text} {ratio}"
                if negative_prompt and "自然语言" not in mode:
                    final_en += f" --no {negative_prompt}"

            st.markdown("### 🇨🇳 中文优化构思")
            st.code(cn_text, language="text", wrap_lines=True)
            
            st.markdown("### 🇺🇸 英文提示词 (直接复制)")
            st.code(final_en, language="text", wrap_lines=True)
            
        except Exception as e:
            st.error(f"出错：{str(e)}")

# ==========================================
# 👉 标签 2：图片反推 (双语版)
# ==========================================
with tab2:
    st.subheader("🖼️ 上传图片，反推 Prompt")
    uploaded_file = st.file_uploader("拖入参考图", type=["jpg", "png"])
    
    if uploaded_file and st.button("🔍 开始反推"):
        current_key = st.session_state.cached_api_key
        
        if not current_key:
            st.error("🚨 请先输入密码！"); st.stop()
            
        try:
            client = OpenAI(api_key=current_key, base_url=base_url)
            img_b64 = encode_image(uploaded_file)
            
            with st.spinner('AI 正在看图...'):
                resp = client.chat.completions.create(
                    model=vision_model,
                    messages=[{
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": "分析这张图。请严格按此格式输出：\nCN: [用中文详细描述画面内容]\nEN: [Midjourney格式的英文关键词，逗号分隔]"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                        ]
                    }]
                )
            
            raw_content = resp.choices[0].message.content
            
            cn_text = "解析中..."
            en_text = raw_content
            if "CN:" in raw_content and "EN:" in raw_content:
                parts = raw_content.split("EN:")
                cn_text = parts[0].replace("CN:", "").strip()
                en_text = parts[1].strip()
            
            c1, c2 = st.columns([1, 2])
            with c1: st.image(uploaded_file, width=150)
            with c2:
                st.markdown("**🇨🇳 中文描述**")
                st.code(cn_text, language="text", wrap_lines=True)
                st.markdown("**🇺🇸 英文 Prompt**")
                st.code(en_text, language="text", wrap_lines=True)
                
        except Exception as e:
            st.error(f"出错：{str(e)}")
