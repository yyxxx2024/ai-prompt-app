import streamlit as st
from openai import OpenAI

# 页面设置
st.set_page_config(page_title="🎨 AI 智能绘图提示词生成器", page_icon="✨")

st.title("✨ AI 提示词魔法师")
st.markdown("输入简单的中文描述，AI 帮你扩写成大师级英文 Prompt。")

# 侧边栏：配置 API Key
with st.sidebar:
    st.header("⚙️ 设置")
    # 这里为了方便演示，兼容 OpenAI 格式（DeepSeek 也用这个格式）
    api_key = st.text_input("请输入你的 API Key", type="password", help="推荐使用 DeepSeek 或 OpenAI 的 Key")
    base_url = st.text_input("API 地址 (Base URL)", value="https://api.deepseek.com", help="如果是 OpenAI 请填 https://api.openai.com/v1")
    model_name = st.text_input("模型名称", value="deepseek-chat", help="例如: deepseek-chat 或 gpt-4o")

# 核心逻辑区
user_input = st.text_area("你想画什么？(支持中文)", height=100, placeholder="例如：一个穿着宇航服的少女，站在火星上，背景是巨大的地球，新海诚风格...")

# 高级选项
col1, col2 = st.columns(2)
with col1:
    ratio = st.selectbox("画幅比例", ["--ar 16:9 (横屏)", "--ar 9:16 (手机)", "--ar 1:1 (方形)", "--ar 2:3 (人像)"])
with col2:
    mode = st.selectbox("优化模式", ["标准扩写", "极简模式 (MJ专用)", "二次元魔法 (Niji)", "写实摄影"])

# 定义 AI 的“人设” (System Prompt) - 这就是智能的核心！
system_prompts = {
    "标准扩写": "你是一个专业的 AI 绘画提示词专家。请将用户的描述翻译成英文，并丰富画面细节、光影、材质和艺术风格。输出格式仅包含英文提示词，关键词用逗号分隔。",
    "极简模式 (MJ专用)": "Translate to English. Keep it concise. Focus on subject + style + lighting. Comma separated.",
    "二次元魔法 (Niji)": "Translate to English. Optimize for anime style (Niji journey). Add tags like: anime style, cel shading, vibrant colors, studio ghibli, makoto shinkai style.",
    "写实摄影": "Translate to English. Optimize for photorealistic photography. Add tags: shot on Sony A7RIV, 85mm lens, f/1.8, cinematic lighting, hyper-realistic, 8k, highly detailed skin texture."
}

if st.button("🚀 开始施法 (生成)", type="primary"):
    if not api_key:
        st.error("请在左侧侧边栏输入 API Key 才能开始工作哦！")
    elif not user_input:
        st.warning("请先告诉我想画什么！")
    else:
        try:
            # 初始化客户端
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            with st.spinner('AI 正在构思画面...'):
                # 拼接用户的需求
                full_prompt = f"用户描述：{user_input}。"
                
                # 调用 AI
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompts[mode]},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.7, # 创造力参数，越高越发散
                )
                
                # 获取结果
                ai_result = response.choices[0].message.content
                
                # 加上比例参数
                final_output = f"{ai_result} {ratio.split(' ')[0]} {ratio.split(' ')[1]}"

            st.success("生成成功！")
            st.code(final_output, language="bash") # 方便复制的框
            
            st.markdown("### 💡 参考解释")
            st.info(f"AI 为你补充了细节，风格选择了：{mode}")

        except Exception as e:
            st.error(f"发生错误：{str(e)}")
            st.markdown("提示：请检查 API Key 是否正确，或者网络是否通畅。")