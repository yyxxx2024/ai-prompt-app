import streamlit as st
from openai import OpenAI

# 1. 页面基本设置
st.set_page_config(page_title="🎨 AI 提示词魔法师 Pro", page_icon="🏗️", layout="centered")
st.title("✨ AI 提示词魔法师 Pro")
st.markdown("输入简单的中文描述，AI 帮你扩写成大师级英文 Prompt。")

# --- 🔐 核心修改：密码验证逻辑 ---
with st.sidebar:
    st.header("🔐 身份验证")
    
    # 获取云端配置的密码和Key（防止报错先给个默认值）
    SYSTEM_PASSWORD = st.secrets.get("APP_PASSWORD", None)
    SYSTEM_API_KEY = st.secrets.get("DEEPSEEK_KEY", None)

    api_key = None
    
    # 1. 输入密码框
    user_password = st.text_input("请输入访问密码", type="password", placeholder="输入密码自动加载 Key")

    # 2. 判断逻辑
    if SYSTEM_PASSWORD and user_password == SYSTEM_PASSWORD:
        api_key = SYSTEM_API_KEY
        st.success("✅ 密码正确！已自动加载 Key")
    else:
        # 如果密码不对，或者没配置密码，允许手动输入
        if user_password:
            st.error("❌ 密码错误")
        st.markdown("---")
        st.caption("或者手动输入 API Key：")
        api_key = st.text_input("API Key", type="password", key="manual_key")

    # API 地址配置
    base_url = st.text_input("API 地址", value="https://api.deepseek.com")
    model_name = st.text_input("模型名称", value="deepseek-chat")
    
    st.markdown("---")
    st.info("💡 **小贴士**：\n- **建筑/写实**：用标签模式。\n- **创意/插画**：用自然语言模式。")

# 3. 主输入区
user_input = st.text_area("你想画什么？(支持中文)", height=100, placeholder="例如：一座海边的白色美术馆，扎哈·哈迪德风格，流线型设计...")

# 4. 模式选择
col1, col2 = st.columns(2)
with col1:
    ratio = st.selectbox("画幅比例", ["--ar 16:9 (横屏)", "--ar 9:16 (手机)", "--ar 1:1 (方形)", "--ar 4:3 (标准)", "--ar 3:2 (摄影)"])
with col2:
    mode = st.selectbox("生成模式 (核心算法)", [
        "建筑设计 (Architecture)",            
        "标准模式 (MJ/SD通用)",               
        "自然语言模式 (Google/Nano Banana 2)", 
        "写实摄影 (Photo)",                   
        "二次元魔法 (Niji)",                  
        "3D 渲染 (3D)",                       
        "极简模式 (MJ V6专用)"                
    ])

# 5. 高级选项区
with st.expander("🎨 点击展开：更多高级选项 (光线、视角、材质)"):
    c1, c2, c3 = st.columns(3)
    with c1:
        lighting = st.selectbox("💡 光线氛围", ["不指定", "自然光 (Natural Light)", "黄金时刻 (Golden Hour)", "电影级布光 (Cinematic)", "阴天漫射光 (Overcast)", "夜景霓虹 (Night Neon)"])
    with c2:
        camera = st.selectbox("📷 镜头视角", ["不指定", "一点透视 (One-point perspective)", "广角宏大 (Wide Angle)", "鸟瞰图 (Aerial View)", "人视角度 (Eye Level)", "微距 (Macro)"])
    with c3:
        material = st.selectbox("🧶 材质/渲染", ["不指定", "混凝土与玻璃 (Concrete & Glass)", "木质纹理 (Wooden)", "砖石结构 (Brick)", "虚幻引擎5 (Unreal Engine 5)", "V-Ray 渲染"])
    
    negative_prompt = st.text_input("🚫 负面提示词", value="text, watermark, blurry, low quality, distorted, ugly, bad architecture")

# 6. 系统提示词逻辑
system_prompts = {
    "建筑设计 (Architecture)": "Translate to English. Target: High-end Architectural Visualization. Add tags: architectural photography, ArchDaily style, Dezeen style, modern architecture, photorealistic, 8k, highly detailed, dramatic lighting, V-Ray render, clean lines, geometric structure.",
    "标准模式 (MJ/SD通用)": "Translate to English. Output purely as a list of comma-separated keywords (tags). Focus on visual descriptors, quality tags, and art styles.",
    "极简模式 (MJ V6专用)": "Translate to English. Keep it extremely concise. Subject + Action + Style + Lighting. Comma separated.",
    "写实摄影 (Photo)": "Translate to English. Target: Photorealism. Add tags: shot on Sony A7RIV, 85mm lens, f/1.8, cinematic lighting, hyper-realistic, 8k, highly detailed skin texture/environment.",
    "3D 渲染 (3D)": "Translate to English. Target: 3D Render. Add tags: octane render, blender, c4d, ray tracing, unreal engine 5, 8k resolution, clean background, 3d masterpiece.",
    "二次元魔法 (Niji)": "Translate to English. Target model: Niji Journey. Add tags: anime style, cel shading, studio ghibli, vibrant colors, highly detailed, 2d.",
    "自然语言模式 (Google/Nano Banana 2)": """
    You are an expert prompt engineer for Google Imagen 2 (Nano Banana) models. 
    1. Translate user description into a rich, descriptive, natural English paragraph.
    2. Do NOT use comma-separated tags. Write complete, fluid sentences.
    3. Start with 'A photorealistic image of...' or 'An architectural rendering of...'.
    4. Seamlessly weave lighting, camera angles, and materials into the description.
    """
}

# 7. 生成按钮逻辑
if st.button("🚀 开始施法 (生成)", type="primary"):
    # 检查 Key 是否存在（无论是自动加载的还是手动输入的）
    if not api_key:
        st.error("🚨 请先输入密码或 API Key！")
    elif not user_input:
        st.warning("请填写你想画什么！")
    else:
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            with st.spinner('AI 正在绘制蓝图...'):
                details = []
                if lighting != "不指定": details.append(f"光线：{lighting}")
                if camera != "不指定": details.append(f"视角：{camera}")
                if material != "不指定": details.append(f"材质：{material}")
                
                full_req = f"用户描述：{user_input}。额外要求：{' '.join(details)}"

                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompts[mode]},
                        {"role": "user", "content": full_req}
                    ],
                    temperature=0.7,
                )
                
                ai_result = response.choices[0].message.content
                final_output = f"{ai_result} {ratio.split(' ')[0]} {ratio.split(' ')[1]}"
                if negative_prompt and "自然语言" not in mode:
                    final_output += f" --no {negative_prompt}"

            st.success("生成成功！")
            st.markdown("### ✅ 生成结果 (点击右上角复制)")
            st.code(final_output, language="text", wrap_lines=True)
            st.caption(f"当前模式：{mode} 🏗️")

        except Exception as e:
            st.error(f"出错啦：{str(e)}")
            st.markdown("提示：如果是密码正确但报错，可能是 API Key 欠费了或填写有误。")
