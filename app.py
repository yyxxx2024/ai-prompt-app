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

# 4. 常用选项区 (放在外面)
col1, col2 = st.columns(2)
with col1:
    ratio = st.selectbox("画幅比例", ["--ar 16:9 (横屏)", "--ar 9:16 (手机)", "--ar 1:1 (方形)", "--ar 4:3 (标准)", "--ar 2:3 (人像)"])
with col2:
    mode = st.selectbox("优化模式", ["标准扩写", "极简模式 (MJ专用)", "二次元魔法 (Niji)", "写实摄影", "3D 渲染"])

# 5. ✨ 高级选项区 (折叠起来，不占位置) ✨
with st.expander("🎨 点击展开：更多高级选项 (光线、视角、材质)"):
    c1, c2, c3 = st.columns(3)
    with c1:
        lighting = st.selectbox("💡 光线氛围", ["不指定", "电影级布光 (Cinematic)", "自然柔光 (Soft Natural)", "赛博霓虹 (Neon)", "伦布朗光 (Rembrandt)", "正午阳光 (Sunny)"])
    with c2:
        camera = st.selectbox("📷 镜头视角", ["不指定", "广角宏大 (Wide Angle)", "微距特写 (Macro)", "无人机俯视 (Drone View)", "鱼眼镜头 (Fisheye)", "正视图 (Front View)"])
    with c3:
        material = st.selectbox("🧶 材质质感", ["不指定", "虚幻引擎5 (Unreal Engine 5)", "磨砂质感 (Matte)", "金属光泽 (Metallic)", "胶片颗粒 (Film Grain)", "水彩 (Watercolor)"])
    
    # 负面提示词 (告诉 AI 不想要什么)
    negative_prompt = st.text_input("🚫 负面提示词 (不希望出现的内容)", value="text, watermark, low quality, bad anatomy, ugly")

# 6. 系统提示词逻辑
system_prompts = {
    "标准扩写": "你是一个 AI 绘画提示词专家。将用户描述翻译为英文，并融入光线、视角等要求。输出英文关键词，用逗号分隔。",
    "极简模式 (MJ专用)": "Translate to English. Concise style. Focus on Subject + Style + Lighting. Comma separated.",
    "二次元魔法 (Niji)": "Translate to English. Anime style, cel shading, studio ghibli, makoto shinkai style, vibrant colors.",
    "写实摄影": "Translate to English. Photorealistic, 8k, highly detailed, shot on Sony A7RIV, 85mm lens, f/1.8.",
    "3D 渲染": "Translate to English. 3D render, octane render, blender, c4d, ray tracing, 8k resolution."
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

