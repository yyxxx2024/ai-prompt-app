import streamlit as st
from openai import OpenAI
import base64

# 1. 页面基本设置 (宽屏模式 + 图标)
st.set_page_config(page_title="🎨 AI 提示词魔法师 Pro", page_icon="🪄", layout="centered")
st.title("✨ AI 提示词魔法师 Pro")

# --- 🛠️ 辅助函数：图片转 Base64 ---
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# --- 🔐 侧边栏：核心设置区 ---
with st.sidebar:
    st.header("🔐 身份验证")
    
    # 从云端 secrets 获取密码和 Key
    SYSTEM_PASSWORD = st.secrets.get("APP_PASSWORD", None)
    SYSTEM_API_KEY = st.secrets.get("API_KEY", None)

    api_key = None
    user_password = st.text_input("访问密码", type="password", placeholder="输入密码自动加载 Key")

    # 密码验证逻辑
    if SYSTEM_PASSWORD and user_password == SYSTEM_PASSWORD:
        api_key = SYSTEM_API_KEY
        st.success("✅ 密码正确！")
    else:
        if user_password: st.error("❌ 密码错误")
        st.caption("或手动输入 API Key：")
        api_key = st.text_input("Key", type="password", label_visibility="collapsed")

    st.markdown("---")
    st.header("⚙️ API 设置 (推荐用中转)")
    
    # 👇 这里是关键：允许同时配置两个模型，方便来回切换
    base_url = st.text_input("API 地址 (Base URL)", value="https://api.deepseek.com", help="如果是中转商，通常填 https://api.xxx.com/v1")
    
    st.caption("📝 **文本生成模型** (推荐 DeepSeek)")
    text_model = st.text_input("Text Model", value="deepseek-chat", label_visibility="collapsed")
    
    st.caption("🖼️ **图片反推模型** (推荐 GPT-4o-mini)")
    vision_model = st.text_input("Vision Model", value="gpt-4o-mini", label_visibility="collapsed")
    
    st.info("💡 **省钱攻略**：\n找一个支持 DeepSeek 和 OpenAI 的中转商，填入统一的 API 地址，就能同时用这两个功能了！")

# --- 🏗️ 功能标签页 ---
tab1, tab2 = st.tabs(["📝 文本生成提示词", "🖼️ 图片反推提示词 (看图)"])

# ==========================================
# 👉 标签 1：文本生成 (DeepSeek/MJ)
# ==========================================
with tab1:
    st.subheader("✍️ 描述画面，生成 Prompt")
    user_input = st.text_area("你想画什么？(支持中文)", height=100, placeholder="例如：一座海边的白色美术馆，扎哈·哈迪德风格，流线型设计...")

    # 模式选择
    col1, col2 = st.columns(2)
    with col1:
        ratio = st.selectbox("画幅比例", ["--ar 16:9 (横屏)", "--ar 9:16 (手机)", "--ar 1:1 (方形)", "--ar 4:3 (标准)", "--ar 3:2 (摄影)"])
    with col2:
        mode = st.selectbox("生成模式", [
            "建筑设计 (Architecture)",            # 🏗️ 你的建筑需求
            "标准模式 (MJ/SD通用)",               # 通用
            "自然语言模式 (Google/Nano Banana 2)", # Google/DALL-E
            "极简模式 (MJ V6专用)",               # 省 token
            "写实摄影 (Photo)",                   # 人像风景
            "二次元魔法 (Niji)",                  # 动漫
            "3D 渲染 (3D)"                        # 设计盲盒
        ])

    # 高级选项 (折叠)
    with st.expander("🎨 高级选项 (光线、视角、材质)"):
        c1, c2, c3 = st.columns(3)
        with c1: lighting = st.selectbox("💡 光线", ["不指定", "自然光", "黄金时刻", "电影级布光", "阴天漫射", "赛博霓虹"])
        with c2: camera = st.selectbox("📷 视角", ["不指定", "一点透视", "广角宏大", "鸟瞰图", "人视角度", "微距"])
        with c3: material = st.selectbox("🧶 材质", ["不指定", "混凝土与玻璃", "木质纹理", "虚幻引擎5", "V-Ray渲染", "磨砂质感"])
        negative_prompt = st.text_input("🚫 负面提示词", value="text, watermark, blurry, low quality, bad anatomy, ugly")

    # 系统提示词逻辑 (AI大脑)
    system_prompts = {
        "建筑设计 (Architecture)": "Translate to English. Target: High-end Architectural Visualization. Add tags: architectural photography, ArchDaily style, Dezeen style, modern architecture, photorealistic, 8k, highly detailed, dramatic lighting, V-Ray render, clean lines, geometric structure.",
        "标准模式 (MJ/SD通用)": "Translate to English. Output purely as a list of comma-separated keywords (tags). Focus on visual descriptors, quality tags.",
        "自然语言模式 (Google/Nano Banana 2)": "You are an expert for Google Imagen 2. Translate to a rich, descriptive, natural English paragraph. Do NOT use comma-separated tags. Write fluid sentences. Start with 'A photorealistic image of...'.",
        "极简模式 (MJ V6专用)": "Translate to English. Keep it extremely concise. Subject + Action + Style + Lighting. Comma separated.",
        "写实摄影 (Photo)": "Translate to English. Target: Photorealism. Add tags: shot on Sony A7RIV, 85mm lens, f/1.8, cinematic lighting, hyper-realistic, 8k, raw photo.",
        "二次元魔法 (Niji)": "Translate to English. Target model: Niji Journey. Add tags: anime style, cel shading, studio ghibli, vibrant colors, highly detailed.",
        "3D 渲染 (3D)": "Translate to English. Target: 3D Render. Add tags: octane render, blender, c4d, unreal engine 5, 8k resolution, 3d masterpiece."
    }

    if st.button("🚀 开始生成 (文本)", type="primary"):
        if not api_key: st.error("请先验证密码或输入 Key！"); st.stop()
        
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # 拼接高级选项
            details = []
            if lighting != "不指定": details.append(f"光线：{lighting}")
            if camera != "不指定": details.append(f"视角：{camera}")
            if material != "不指定": details.append(f"材质：{material}")
            full_req = f"用户描述：{user_input}。额外要求：{' '.join(details)}"

            with st.spinner(f'AI ({text_model}) 正在构思...'):
                response = client.chat.completions.create(
                    model=text_model, # 使用侧边栏设置的文本模型
                    messages=[
                        {"role": "system", "content": system_prompts[mode]},
                        {"role": "user", "content": full_req}
                    ],
                    temperature=0.7
                )
                
                ai_result = response.choices[0].message.content
                final_output = f"{ai_result} {ratio.split(' ')[0]} {ratio.split(' ')[1]}"
                if negative_prompt and "自然语言" not in mode:
                    final_output += f" --no {negative_prompt}"

            st.success("生成成功！")
            st.markdown("### ✅ 结果 (右上角复制)")
            st.code(final_output, language="text", wrap_lines=True)

        except Exception as e:
            st.error(f"出错：{str(e)}")

# ==========================================
# 👉 标签 2：图片反推 (GPT-4o/Claude)
# ==========================================
with tab2:
    st.subheader("🖼️ 上传图片，反推 Prompt")
    st.info(f"💡 当前使用模型：**{vision_model}** (请确保你的 Key 支持该模型)")

    uploaded_file = st.file_uploader("拖入参考图", type=["jpg", "png", "jpeg"])
    reverse_mode = st.radio("输出格式", ["MJ 标签格式 (逗号分隔)", "自然语言描述 (写作文)"], horizontal=True)

    if uploaded_file and st.button("🔍 开始反推", type="primary"):
        if not api_key: st.error("请先验证密码！"); st.stop()
        
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            base64_image = encode_image(uploaded_file)
            
            # 定义反推指令
            if "标签" in reverse_mode:
                prompt_text = "分析这张图的主体、风格、光影、材质。直接输出英文关键词，用逗号分隔。"
            else:
                prompt_text = "详细描述这张图片，包括主体、环境、光影和风格。请输出一段通顺优美的英文描述（适合 DALL-E 3 或 Google GenAI）。"

            with st.spinner(f'AI ({vision_model}) 正在观察图片...'):
                response = client.chat.completions.create(
                    model=vision_model, # 使用侧边栏设置的视觉模型
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_text},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]
                        }
                    ],
                    max_tokens=500
                )
            
            result_text = response.choices[0].message.content
            
            c1, c2 = st.columns([1, 2])
            with c1: st.image(uploaded_file, caption="原图", use_container_width=True)
            with c2:
                st.success("反推完成！")
                st.code(result_text, language="text", wrap_lines=True)

        except Exception as e:
            st.error("❌ 失败了")
            st.error(f"错误详情：{str(e)}")
            st.warning("常见原因：你使用的 API Key 不支持视觉模型，或者 Base URL 填的是 DeepSeek 官方地址（DeepSeek 暂不支持看图）。建议使用支持 GPT-4o-mini 的中转服务。")
