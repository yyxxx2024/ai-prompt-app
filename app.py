import streamlit as st
from openai import OpenAI
import base64

# 1. 页面设置
st.set_page_config(page_title="🎨 AI 提示词魔法师 Pro", page_icon="🏗️", layout="centered")
st.title("✨ AI 提示词魔法师 Pro")

# --- 🛠️ 辅助函数 ---
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# --- 🔐 身份验证逻辑 ---
if "cached_api_key" not in st.session_state:
    st.session_state.cached_api_key = None

with st.sidebar:
    st.header("🔐 身份验证")
    SYSTEM_PASSWORD = st.secrets.get("APP_PASSWORD", None)
    SYSTEM_API_KEY = st.secrets.get("API_KEY", None)
    
    user_password = st.text_input("🔑 访问密码", type="password", placeholder="输入密码，自动加载 Key")
    manual_key = st.text_input("或手动输入 Key", type="password", label_visibility="collapsed")

    if SYSTEM_PASSWORD and user_password == SYSTEM_PASSWORD:
        if SYSTEM_API_KEY:
            st.session_state.cached_api_key = SYSTEM_API_KEY
            st.success("✅ 密码正确！令牌已锁定")
        else:
            st.error("⚠️ 云端 Secrets 未配置 API_KEY")
    elif manual_key:
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
# 👉 标签 1：文本生成 (建筑增强版)
# ==========================================
with tab1:
    st.subheader("✍️ 描述画面，生成 Prompt")
    user_input = st.text_area("你想画什么？", height=100, placeholder="例如：一个坐落在悬崖边的美术馆，扎哈风格...")

    c1, c2 = st.columns(2)
    with c1: 
        ratio = st.selectbox("画幅", ["--ar 16:9 (横屏)", "--ar 4:3 (标准)", "--ar 3:2 (摄影)", "--ar 9:16 (手机)", "--ar 1:1 (方形)"])
    with c2: 
        # 👇 核心：增加了“建筑效果图专用”
        mode = st.selectbox("模式", [
            "🏗️ 建筑效果图专用 (ArchViz)", 
            "标准模式 (MJ/SD)", 
            "自然语言 (Google)", 
            "二次元 (Niji)", 
            "写实摄影", 
            "3D渲染"
        ])

    # ✨✨✨ 动态高级选项 (根据模式自动切换) ✨✨✨
    with st.expander("🎨 点击展开：高级参数配置 (已根据模式自动优化)"):
        
        # 🔴 情况 A：如果是【建筑模式】，显示建筑师专用的 6 大参数
        if "建筑" in mode:
            st.caption("🏗️ **建筑师专用参数面板**")
            ac1, ac2, ac3 = st.columns(3)
            with ac1:
                arch_view = st.selectbox("📐 构图视点", ["不指定", "人视角度 (Eye Level)", "半鸟瞰 (Semi-Aerial)", "顶视图/总平 (Top View)", "虫视/仰视 (Worm's Eye)", "一点透视 (One Point)", "轴测图 (Isometric)"])
            with ac2:
                arch_time = st.selectbox("🌤️ 天气时刻", ["不指定", "黄金时刻 (Golden Hour)", "蓝调时刻 (Blue Hour)", "正午晴天 (Sunny Noon)", "阴天漫射 (Overcast)", "雨夜 (Rainy Night)", "雾天 (Foggy)"])
            with ac3:
                arch_env = st.selectbox("🌳 周边环境", ["不指定", "繁华街道 (Busy Street)", "森林景观 (Forest)", "海滨/水岸 (Waterfront)", "雪景 (Snowy)", "荒漠 (Desert)", "极简棚拍 (Studio)"])
            
            ac4, ac5, ac6 = st.columns(3)
            with ac4:
                arch_style = st.selectbox("🏛️ 建筑风格", ["不指定", "现代极简 (Minimalist)", "参数化设计 (Parametric)", "粗野主义 (Brutalist)", "工业风 (Industrial)", "未来主义 (Futuristic)", "传统中式 (Traditional Chinese)"])
            with ac5:
                arch_mat = st.selectbox("🧶 主体材质", ["不指定", "清水混凝土 (Concrete)", "玻璃幕墙 (Glass Facade)", "木格栅 (Wooden Louvers)", "白墙 (White Stucco)", "红砖 (Red Brick)", "耐候钢 (Corten Steel)"])
            with ac6:
                arch_render = st.selectbox("🖥️ 渲染引擎风格", ["不指定", "V-Ray 逼真渲染", "Unreal Engine 5", "Lumion 风格", "手绘草图 (Sketch)", "水彩渲染 (Watercolor)", "模型风 (Maquette)"])

        # 🔵 情况 B：如果是其他模式，显示通用的参数
        else:
            st.caption("🎨 **通用高级参数**")
            col_a, col_b, col_c = st.columns(3)
            with col_a: 
                lighting = st.selectbox("💡 光线", ["不指定", "自然光", "电影光", "黄金时刻", "霓虹光", "柔光"])
            with col_b: 
                camera = st.selectbox("📷 视角", ["不指定", "广角", "微距", "鸟瞰", "平视", "鱼眼"])
            with col_c: 
                mood = st.selectbox("🎭 氛围", ["不指定", "梦幻", "史诗", "阴郁", "宁静", "活力"])

        st.markdown("---")
        st.caption("🎛️ **Midjourney 参数微调**")
        m1, m2 = st.columns(2)
        with m1: stylize = st.slider("风格化 (--s)", 0, 1000, 250)
        with m2: chaos = st.slider("多样性 (--c)", 0, 100, 0)
        
        negative_prompt = st.text_input("🚫 负面提示词", value="text, watermark, blurry, low quality, bad anatomy, ugly, distorted structures")

    # 🔥 核心指令
    base_instruction = """
    You are an expert AI prompt engineer.
    IMPORTANT: Output exactly two parts:
    CN: [Optimized Chinese description]
    EN: [Final English prompt]
    """
    
    # 模式对应的 Prompt 逻辑
    mode_rules = {
        "🏗️ 建筑效果图专用 (ArchViz)": """
        For EN: You are an Architectural Visualization Expert. 
        1. Use professional ArchViz terminology (e.g., 'curtain wall', 'cantilever', 'volumetric lighting').
        2. Target style: ArchDaily, Dezeen, Behance high-end rendering.
        3. Format: Comma-separated tags. 
        4. Always add: '8k resolution, photorealistic, architectural photography, highly detailed'.
        """,
        "标准模式 (MJ/SD)": "For EN: Output comma-separated keywords. Visual descriptors.",
        "自然语言 (Google)": "For EN: Write a rich, descriptive English paragraph.",
        "二次元 (Niji)": "For EN: Anime style, cel shading, vibrant colors.",
        "写实摄影": "For EN: Photorealistic, 8k, shot on Sony A7RIV.",
        "3D渲染": "For EN: 3D render, blender, c4d, octane render."
    }
    
    sys_prompt = base_instruction + mode_rules.get(mode, mode_rules["标准模式 (MJ/SD)"])

    if st.button("🚀 生成双语提示词", type="primary"):
        current_key = st.session_state.cached_api_key
        if not current_key: st.error("🚨 请先输入密码！"); st.stop()
        
        try:
            client = OpenAI(api_key=current_key, base_url=base_url)
            
            # 👇 智能拼接参数（根据模式不同，拼接不同的变量）
            details = []
            
            if "建筑" in mode:
                # 拼接建筑专用参数
                if arch_view != "不指定": details.append(f"View: {arch_view}")
                if arch_time != "不指定": details.append(f"Time: {arch_time}")
                if arch_env != "不指定": details.append(f"Environment: {arch_env}")
                if arch_style != "不指定": details.append(f"Style: {arch_style}")
                if arch_mat != "不指定": details.append(f"Material: {arch_mat}")
                if arch_render != "不指定": details.append(f"Render Style: {arch_render}")
            else:
                # 拼接通用参数
                if lighting != "不指定": details.append(f"Lighting: {lighting}")
                if camera != "不指定": details.append(f"Camera: {camera}")
                if mood != "不指定": details.append(f"Mood: {mood}")
            
            full_req = f"User Request: {user_input}. Specific Requirements: {', '.join(details)}"

            with st.spinner('AI 正在绘制蓝图...'):
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
                
                final_en = f"{en_text} {ratio.split(' ')[0]}"
                if "自然语言" not in mode:
                    final_en += f" --s {stylize} --c {chaos}"
                    if negative_prompt: final_en += f" --no {negative_prompt}"

            st.markdown("### 🇨🇳 中文构思")
            st.code(cn_text, language="text", wrap_lines=True)
            st.markdown("### 🇺🇸 英文 Prompt (可以直接复制)")
            st.code(final_en, language="text", wrap_lines=True)
            
        except Exception as e:
            st.error(f"出错：{str(e)}")

# ==========================================
# 👉 标签 2：图片反推 (保持不变)
# ==========================================
with tab2:
    st.subheader("🖼️ 上传图片，反推 Prompt")
    uploaded_file = st.file_uploader("拖入参考图", type=["jpg", "png"])
    if uploaded_file and st.button("🔍 开始反推"):
        current_key = st.session_state.cached_api_key
        if not current_key: st.error("请先输入密码！"); st.stop()
        try:
            client = OpenAI(api_key=current_key, base_url=base_url)
            img_b64 = encode_image(uploaded_file)
            with st.spinner('AI 正在看图...'):
                resp = client.chat.completions.create(
                    model=vision_model,
                    messages=[{"role": "user", "content": [{"type": "text", "text": "分析这张图。输出格式：\nCN: [中文描述]\nEN: [MJ关键词]"}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}]}]
                )
            raw = resp.choices[0].message.content
            cn, en = raw, raw
            if "EN:" in raw: cn, en = raw.split("EN:")[0].replace("CN:", ""), raw.split("EN:")[1]
            c1, c2 = st.columns([1, 2])
            with c1: st.image(uploaded_file, width=150)
            with c2: st.code(cn.strip(), language="text", wrap_lines=True); st.code(en.strip(), language="text", wrap_lines=True)
        except Exception as e: st.error(f"出错：{e}")
