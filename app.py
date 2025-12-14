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
        else:
