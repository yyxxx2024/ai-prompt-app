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
tab1, tab2 = st.tabs(["📝 文本生成 (双方案版)", "🖼️ 图片反推 (看图)"])

# ==========================================
# 👉 标签 1：文本生成 (双方案版)
# ==========================================
with tab1:
    st.subheader("✍️ 描述画面，生成 2 种方案")
    user_input = st.text_area("你想画什么？", height=100, placeholder="例如：一个坐落在悬崖边的美术馆，扎哈风格...")

    c1, c2 = st.columns(2)
    with c1: 
        ratio = st.selectbox("画幅", ["--ar 16:9 (横屏)", "--ar 4:3 (标准)", "--ar 3:2 (摄影)", "--ar 9:16 (手机)", "--ar 1:1 (方形)"])
    with c2: 
        mode = st.selectbox("模式", [
            "🏗️ 建筑效果图专用 (ArchViz)", 
            "标准模式 (MJ/SD)", 
            "自然语言 (Google)", 
            "二次元 (Niji)", 
            "写实摄影", 
            "3D渲染"
        ])

    # ✨ 动态高级选项
    with st.expander("🎨 点击展开：高级参数配置"):
        # 🔴 情况 A：建筑模式
        if "建筑" in mode:
            st.caption("🏗️ **建筑师专用参数**")
            ac1, ac2, ac3 = st.columns(3)
            with ac1: arch_view = st.selectbox("📐 视点", ["不指定", "人视 (Eye Level)", "半鸟瞰 (Semi-Aerial)", "顶视 (Top View)", "虫视 (Worm's Eye)", "一点透视"])
            with ac2: arch_time = st.selectbox("🌤️ 时刻", ["不指定", "黄金时刻", "蓝调时刻", "正午", "阴天", "雨夜", "雾天"])
            with ac3: arch_env = st.selectbox("🌳 环境", ["不指定", "街道", "森林", "水岸", "雪景", "荒漠", "极简棚拍"])
            
            ac4, ac5, ac6 = st.columns(3)
            with ac4: arch_style = st.selectbox("🏛️ 风格", ["不指定", "极简", "参数化", "粗野主义", "工业风", "未来主义", "新中式"])
            with ac5: arch_mat = st.selectbox("🧶 材质", ["不指定", "清水混凝土", "玻璃幕墙", "木格栅", "白墙", "红砖", "耐候钢"])
            with ac6: arch_render = st.selectbox("🖥️ 渲染", ["不指定", "V-Ray 逼真", "UE5", "Lumion", "手绘草图", "水彩"])
        
        # 🔵 情况 B：通用模式 (注意这里必须要有缩进！)
        else:
            st.caption("🎨 **通用参数**")
            col_a, col_b, col_c = st.columns(3)
            with col_a: lighting = st.selectbox("💡 光线", ["不指定", "自然光", "电影光", "黄金时刻", "霓虹光", "柔光"])
            with col_b: camera = st.selectbox("📷 视角", ["不指定", "广角", "微距", "鸟瞰", "平视", "鱼眼"])
            with col_c: mood = st.selectbox("🎭 氛围", ["不指定", "梦幻", "史诗", "阴郁", "宁静", "活力"])

        st.markdown("---")
        m1, m2 = st.columns(2)
        with m1: stylize = st.slider("风格化 (--s)", 0, 1000, 250)
        with m2: chaos = st.slider("多样性 (--c)", 0, 100, 0)
        negative_prompt = st.text_input("🚫 负面提示词", value="text, watermark, blurry, low quality, bad anatomy, ugly, distorted structures")

    # 🔥🔥 核心升级：双方案指令 🔥🔥
    base_instruction = """
    You are an expert AI prompt engineer.
    IMPORTANT: You must generate TWO different prompt options:
    
    1. Plan A (Faithful): Strictly follows the user's description. Precise and clean.
    2. Plan B (Creative): enhance the lighting, atmosphere, and artistic details significantly. Make it a masterpiece.

    STRICT OUTPUT FORMAT (Do not change these markers):
    ===PLAN_A_CN===
    [Chinese description for Plan A]
    ===PLAN_A_EN===
    [English Prompt for Plan A]
    ===PLAN_B_CN===
    [Chinese description for Plan B]
    ===PLAN_B_EN===
    [English Prompt for Plan B]
    """
    
    mode_rules = {
        "🏗️ 建筑效果图专用 (ArchViz)": "Target: ArchViz. Tags: ArchDaily style, V-Ray, 8k, photorealistic.",
        "标准模式 (MJ/SD)": "Target: General Art. Format: Comma-separated keywords.",
        "自然语言 (Google)": "Target: Natural Language. Format: Descriptive paragraphs.",
        "二次元 (Niji)": "Target: Anime. Tags: Anime style, cel shading, vibrant.",
        "写实摄影": "Target: Photography. Tags: Shot on Sony A7RIV, 8k.",
        "3D渲染": "Target: 3D. Tags: Octane render, C4D, Blender."
    }
    
    sys_prompt = base_instruction + mode_rules.get(mode, "")

    if st.button("🚀 生成两种方案", type="primary"):
        current_key = st.session_state.cached_api_key
        if not current_key: st.error("🚨 请先输入密码！"); st.stop()
        
        try:
            client = OpenAI(api_key=current_key, base_url=base_url)
            
            # 拼接参数
            details = []
            if "建筑" in mode:
                # 建筑模式参数拼接
                if arch_view != "不指定": details.append(f"View: {arch_view}")
                if arch_time != "不指定": details.append(f"Time: {arch_time}")
                if arch_env != "不指定": details.append(f"Env: {arch_env}")
                if arch_style != "不指定": details.append(f"Style: {arch_style}")
                if arch_mat != "不指定": details.append(f"Mat: {arch_mat}")
                if arch_render != "不指定": details.append(f"Render: {arch_render}")
            else:
                # 通用模式参数拼接
                if lighting != "不指定": details.append(f"Light: {lighting}")
                if camera != "不指定": details.append(f"Cam: {camera}")
                if mood != "不指定": details.append(f"Mood: {mood}")
            
            full_req = f"User Request: {user_input}. Requirements: {', '.join(details)}"

            with st.spinner('AI 正在构思两种方案...'):
                resp = client.chat.completions.create(
                    model=text_model,
                    messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": full_req}]
                )
                
                raw = resp.choices[0].message.content
                
                # 🔥🔥 核心升级：双方案解析逻辑 🔥🔥
                p1_cn, p1_en, p2_cn, p2_en = "解析中...", "Generating...", "解析中...", "Generating..."
                
                try:
                    if "===PLAN_A_EN===" in raw:
                        # 暴力切割字符串
                        part1 = raw.split("===PLAN_B_CN===")[0]
                        part2 = raw.split("===PLAN_B_CN===")[1]
                        
                        p1_cn = part1.split("===PLAN_A_EN===")[0].replace("===PLAN_A_CN===", "").strip()
                        p1_en = part1.split("===PLAN_A_EN===")[1].strip()
                        
                        p2_cn = part2.split("===PLAN_B_EN===")[0].strip()
                        p2_en = part2.split("===PLAN_B_EN===")[1].strip()
                except:
                    st.warning("AI 返回格式有些小问题，但我尽力解析了")

                # 拼接后缀参数
                suffix = f" {ratio.split(' ')[0]}"
                if "自然语言" not in mode:
                    suffix += f" --s {stylize} --c {chaos}"
                    if negative_prompt: suffix += f" --no {negative_prompt}"
                
                final_p1 = p1_en + suffix
                final_p2 = p2_en + suffix

            # ✨✨✨ 展示两个方案 ✨✨✨
            st.success("✅ 生成完成！为您提供两种思路：")
            
            st.markdown("### 🅰️ 方案 A：精准还原 (Faithful)")
            st.info(f"💡 思路：{p1_cn}")
            st.code(final_p1, language="text", wrap_lines=True)
            
            st.divider() # 分割线
            
            st.markdown("### 🅱️ 方案 B：艺术增强 (Creative)")
            st.info(f"✨ 思路：{p2_cn}")
            st.code(final_p2, language="text", wrap_lines=True)
            
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
