import streamlit as st
from openai import OpenAI

# 1. 页面基本设置
st.set_page_config(page_title="🎨 AI 提示词魔法师 Pro", page_icon="✨", layout="centered")
st.title("✨ AI 提示词魔法师 Pro")
st.markdown("输入简单的中文描述，AI 帮你扩写成大师级英文 Prompt。")

# 2. 侧边栏：API 设置
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("请输入 API Key", type="password", help="推荐使用 DeepSeek 或 OpenAI")
    base_url = st.text_input("API 地址", value="https://api.deepseek.com")
    model_name = st.text_input("模型名称", value="deepseek-chat")
    st.markdown("---")
    st.info("💡 提示：'自然语言模式' 适合 Google Imagen / DALL-E 3；'标准模式' 适合 Midjourney / SD。")

# 3. 主输入区
user_input = st.text_area("你想画什么？(支持中文)", height=100, placeholder="例如：一个自建房建筑，极简风格...")

# 4. 模式选择 (全能版：保留了所有之前的选项 + Google 模式)
col1, col2 = st.columns(2)
with col1:
    ratio = st.selectbox("画幅比例", ["--ar 16:9 (横屏)", "--ar 9:16 (手机)", "--ar 1:1 (方形)", "--ar 4:3 (标准)", "--ar 2:3 (人像)"])
with col2:
    mode = st.selectbox("生成模式 (核心算法)", [
        "标准模式 (MJ/SD通用)",               # 最稳的通用版
        "自然语言模式 (Google/Nano Banana 2)", # ✨ 新增：写作文模式
        "极简模式 (MJ V6专用)",               # 省 token 版
        "二次元魔法 (Niji)",                  # 动漫专用
        "写实摄影 (Photo)",                   # 真人摄影专用
        "3D 渲染 (3D)"                        # C4D/Blender 风
    ])

# 5. ✨ 高级选项区 (折叠起来，不占位置)
with st.expander("🎨 点击展开：更多高级选项 (光线、视角、材质)"):
    c1, c2, c3 = st.columns(3)
    with c1:
        lighting = st.selectbox("💡 光线氛围", ["不指定", "电影级布光 (Cinematic)", "自然柔光 (Soft Natural)", "赛博霓虹 (Neon)", "伦布朗光 (Rembrandt)", "正午阳光 (Sunny)"])
    with c2:
        camera = st.selectbox("📷 镜头视角", ["不指定", "广角宏大 (Wide Angle)", "微距特写 (Macro)", "无人机俯视 (Drone View)", "鱼眼镜头 (Fisheye)", "正视图 (Front View)"])
    with c3:
        material = st.selectbox("🧶 材质质感", ["不指定", "虚幻引擎5 (Unreal Engine 5)", "磨砂质感 (Matte)", "金属光泽 (Metallic)", "胶片颗粒 (Film Grain)", "水彩 (Watercolor)"])
    
    # 负面提示词
    negative_prompt = st.text_input("🚫 负面提示词 (不希望出现的内容)", value="text, watermark, low quality, bad anatomy, ugly")

# 6. 系统提示词逻辑 (定义 AI 的大脑)
system_prompts = {
    # 🟢 === 标签流 (Midjourney / Stable Diffusion) ===
    "标准模式 (MJ/SD通用)": "You are an AI prompt expert. Translate user description to English. Output purely as a list of comma-separated keywords (tags). Focus on visual descriptors, quality tags, and art styles. Do NOT use full sentences.",
    
    "极简模式 (MJ V6专用)": "Translate to English. Keep it extremely concise. Subject + Action + Style + Lighting. No filler words. Comma separated.",
    
    "二次元魔法 (Niji)": "Translate to English. Target model: Niji Journey (Anime). Add tags: anime style, cel shading, studio ghibli, makoto shinkai style, vibrant colors, highly detailed, 2d.",
    
    "写实摄影 (Photo)": "Translate to English. Target: Photorealism. Add tags: shot on Sony A7RIV, 85mm lens, f/1.8, cinematic lighting, hyper-realistic, 8k, highly detailed skin texture, raw photo.",
    
    "3D 渲染 (3D)": "Translate to English. Target: 3D Render. Add tags: octane render, blender, c4d, ray tracing, unreal engine 5, 8k resolution, clean background, 3d masterpiece.",

    # 🔵 === 自然语言流 (Google Imagen / Nano Banana / DALL-E) ===
    "自然语言模式 (Google/Nano Banana 2)": """
    You are an expert prompt engineer for Google Imagen 2 (Nano Banana) models. 
    1. Translate the user's description into a rich, descriptive, natural English paragraph.
    2. Do NOT use comma-separated tags. Write complete, fluid sentences.
    3. Start with 'A photorealistic image of...' or 'A creative illustration of...'.
    4. Seamlessly weave the user's selected lighting, camera angles, and materials into the narrative description naturally.
    """
}

# 7. 生成按钮与逻辑
if st.button("🚀 开始施法 (生成)", type="primary"):
    if not api_key:
        st.error("请在左侧填入 API Key！")
    elif not user_input:
        st.warning("请填写你想画什么！")
    else:
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            with st.spinner('AI 正在构思画面...'):
                # 收集用户的高级选项
                details = []
                if lighting != "不指定": details.append(f"光线要求：{lighting}")
                if camera != "不指定": details.append(f"镜头视角：{camera}")
                if material != "不指定": details.append(f"材质质感：{material}")
                
                # 拼接给 AI 的总指令
                full_req = f"用户描述：{user_input}。额外要求：{' '.join(details)}"

                # 调用 AI
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompts[mode]},
                        {"role": "user", "content": full_req}
                    ],
                    temperature=0.7,
                )
                
                ai_result = response.choices[0].message.content
                
                # 最终组合结果
                final_output = f"{ai_result} {ratio.split(' ')[0]} {ratio.split(' ')[1]}"
                
                # 只有非自然语言模式，通常才加 --no 参数 (Google 模型一般直接写在句子里，但加上也不报错)
                if negative_prompt:
                    final_output += f" --no {negative_prompt}"

            st.success("生成成功！")
            
            # ✨ 这里使用了 st.code 并开启 wrap_lines，实现了【大框 + 自动换行 + 复制按钮】
            st.markdown("### ✅ 生成结果 (点击右上角复制)")
            st.code(final_output, language="text", wrap_lines=True)
            
            st.caption(f"当前模式：{mode} | 已应用高级选项")

        except Exception as e:
            st.error(f"出错啦：{str(e)}")
            st.markdown("提示：请检查 API Key 是否正确，或网络是否通畅。")
