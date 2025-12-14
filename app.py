import streamlit as st
from openai import OpenAI

# 1. 页面基本设置
st.set_page_config(page_title="🎨 AI 提示词魔法师 Pro", page_icon="✨")
st.title("✨ AI 提示词魔法师 Pro")
st.markdown("输入简单的中文描述，AI 帮你扩写成大师级英文 Prompt。")

# 2. 侧边栏：API 设置
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("请输入你的 API Key", type="password", help="推荐使用 DeepSeek 或 OpenAI")
    base_url = st.text_input("API 地址", value="https://api.deepseek.com")
    model_name = st.text_input("模型名称", value="deepseek-chat")
    st.markdown("---")
    st.markdown("💡 *提示：如果是 MJ 作图，推荐选极简模式。*")

# 3. 主输入区
user_input = st.text_area("你想画什么？(支持中文)", height=100, placeholder="例如：一个自建房建筑，极简风格...")

# 4. 模式选择 (清楚区分 MJ 和 Google)
col1, col2 = st.columns(2)
with col1:
    ratio = st.selectbox("画幅比例", ["--ar 16:9 (横屏)", "--ar 9:16 (手机)", "--ar 1:1 (方形)", "--ar 4:3 (标准)", "--ar 2:3 (人像)"])
with col2:
    # 这里把选项名字改得非常直观
    mode = st.selectbox("生成模式 (核心算法)", [
        "标准标签模式 (MJ/SD通用)", 
        "自然语言模式 (Google Nano Banana 2)", 
        "极简短语模式 (MJ V6专用)", 
        "二次元动漫 (Niji)", 
        "写实摄影 (Photo)", 
        "3D 渲染 (3D)"
    ])

# 5. ✨ 高级选项区 (保持不变，这里省略...)
# (你的 with st.expander... 代码保持原样即可)
# ...

# 6. 系统提示词逻辑 (这里定义了两种截然不同的写法)
system_prompts = {
    # 🟢 方案 A：Midjourney / Stable Diffusion 风格
    # 特点：全是关键词，用逗号隔开，强调词汇堆砌
    "标准标签模式 (MJ/SD通用)": "You are an AI prompt expert. Translate user description to English. Output purely as a list of comma-separated keywords (tags). Focus on visual descriptors, quality tags, and art styles. Do NOT use full sentences.",
    
    "极简短语模式 (MJ V6专用)": "Translate to English. Keep it extremely concise. Subject + Action + Style + Lighting. No filler words. Comma separated.",
    
    "二次元动漫 (Niji)": "Translate to English. Target model: Niji Journey. Add tags: anime style, cel shading, studio ghibli, makoto shinkai style, vibrant colors, highly detailed.",
    
    "写实摄影 (Photo)": "Translate to English. Target: Photorealism. Add tags: shot on Sony A7RIV, 85mm lens, f/1.8, cinematic lighting, hyper-realistic, 8k, highly detailed skin texture.",
    
    "3D 渲染 (3D)": "Translate to English. Target: 3D Render. Add tags: octane render, blender, c4d, ray tracing, unreal engine 5, 8k resolution, clean background.",

    # 🔵 方案 B：Google Imagen (Nano Banana 2) / DALL-E 3 风格
    # 特点：像写作文一样，通顺优美的长句子，不要逗号分隔
    "自然语言模式 (Google Nano Banana 2)": """
    You are an expert prompt engineer for Google Imagen 2 (Nano Banana) models. 
    1. Translate the user's description into a rich, descriptive, natural English paragraph.
    2. Do NOT use comma-separated tags. Write complete, fluid sentences.
    3. Start with 'A photorealistic image of...' or 'An expressive painting of...'.
    4. Seamlessly weave lighting, camera angles, and textures into the narrative description.
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
            
            with st.spinner('AI 正在调配颜色...'):
                # 聪明地拼接用户的要求
                details = []
                if lighting != "不指定": details.append(f"光线要求：{lighting}")
                if camera != "不指定": details.append(f"镜头视角：{camera}")
                if material != "不指定": details.append(f"材质质感：{material}")
                
                full_req = f"用户描述：{user_input}。{' '.join(details)}"

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
                
                # 最终组合：AI结果 + 负面词参数 + 比例
                # (注意：如果是 MJ，负面词通常用 --no 参数，这里简单起见我们只处理比例)
                # 为了更通用，我们把负面词放在提示词末尾，或者用 --no 格式
                
                final_output = f"{ai_result} --ar {ratio.split(' ')[1]}"
                if negative_prompt:
                    final_output += f" --no {negative_prompt}"

            st.success("生成成功！")
            
            # 这里是你要求的【大框 + 自动换行】
            st.markdown("### ✅ 生成结果 (点击右上角复制)")
            st.code(final_output, language="text", wrap_lines=True)
            
            st.info(f"✨ 已应用高级选项：{lighting} | {camera} | {material}")

        except Exception as e:
            st.error(f"出错啦：{str(e)}")



