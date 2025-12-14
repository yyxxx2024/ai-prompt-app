import streamlit as st
from openai import OpenAI
import base64
import json
import os

# 1. 页面设置
st.set_page_config(page_title="🎨 AI 提示词魔法师 Pro", page_icon="🏗️", layout="centered")
st.title("✨ AI 提示词魔法师 Pro")

# --- 🛠️ 辅助函数：JSON 存储系统 ---
FILE_PATH = "my_fav_prompts.json"

def load_data():
    """读取收藏数据"""
    if not os.path.exists(FILE_PATH):
        return []
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    """保存收藏数据"""
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# --- 🔐 身份验证逻辑 ---
if "cached_api_key" not in st.session_state:
    st.session_state.cached_api_key = None
# 初始化生成结果缓存 (防止刷新后结果消失)
if "last_results" not in st.session_state:
    st.session_state.last_results = None

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
tab1, tab2, tab3 = st.tabs(["📝 文本生成 (双方案)", "🖼️ 图片反推", "🌟 我的提示词宝库"])

# ==========================================
# 👉 标签 1：文本生成 (含一键收藏)
# ==========================================
with tab1:
    st.subheader("✍️ 描述画面，生成 2 种方案")
    user_input = st.text_area("你想画什么？", height=100, placeholder="例如：一个坐落在悬崖边的美术馆，扎哈风格...")

    c1, c2 = st.columns(2)
    with c1: 
        ratio = st.selectbox("画幅", ["--ar 16:9", "--ar 4:3", "--ar 3:2", "--ar 9:16", "--ar 1:1"])
    with c2: 
        mode = st.selectbox("模式", [
            "🏗️ 建筑效果图 (ArchViz)", "标准模式 (MJ/SD)", 
            "自然语言 (Google)", "二次元 (Niji)", "写实摄影", "3D渲染"
        ])

    # 高级选项
    with st.expander("🎨 点击展开：高级参数配置"):
        if "建筑" in mode:
            ac1, ac2, ac3 = st.columns(3)
            with ac1: arch_view = st.selectbox("📐 视点", ["不指定", "人视", "半鸟瞰", "顶视", "虫视", "一点透视"])
            with ac2: arch_time = st.selectbox("🌤️ 时刻", ["不指定", "黄金时刻", "蓝调时刻", "正午", "阴天", "雨夜"])
            with ac3: arch_env = st.selectbox("🌳 环境", ["不指定", "街道", "森林", "水岸", "雪景", "荒漠"])
            
            ac4, ac5, ac6 = st.columns(3)
            with ac4: arch_style = st.selectbox("🏛️ 风格", ["不指定", "极简", "参数化", "粗野主义", "工业风", "未来主义"])
            with ac5: arch_mat = st.selectbox("🧶 材质", ["不指定", "混凝土", "玻璃幕墙", "木格栅", "白墙", "红砖", "耐候钢"])
            with ac6: arch_render = st.selectbox("🖥️ 渲染", ["不指定", "V-Ray 逼真", "UE5", "Lumion", "手绘", "水彩"])
        else:
            col_a, col_b, col_c = st.columns(3)
            with col_a: lighting = st.selectbox("💡 光线", ["不指定", "自然光", "电影光", "黄金时刻", "霓虹光"])
            with col_b: camera = st.selectbox("📷 视角", ["不指定", "广角", "微距", "鸟瞰", "平视"])
            with col_c: mood = st.selectbox("🎭 氛围", ["不指定", "梦幻", "史诗", "阴郁", "宁静"])

        st.markdown("---")
        m1, m2 = st.columns(2)
        with m1: stylize = st.slider("风格化 (--s)", 0, 1000, 250)
        with m2: chaos = st.slider("多样性 (--c)", 0, 100, 0)
        negative_prompt = st.text_input("🚫 负面提示词", value="text, watermark, blurry, low quality, bad anatomy, ugly, distorted structures")

    # Prompt Template
    base_instruction = """
    You are an expert AI prompt engineer. Generate TWO options:
    1. Plan A (Faithful): Precise and clean.
    2. Plan B (Creative): Artistic masterpiece.
    
    STRICT OUTPUT FORMAT:
    ===PLAN_A_CN=== [Chinese A]
    ===PLAN_A_EN=== [English Prompt A]
    ===PLAN_B_CN=== [Chinese B]
    ===PLAN_B_EN=== [English Prompt B]
    """
    
    mode_rules = {
        "🏗️ 建筑效果图 (ArchViz)": "Target: ArchViz. Tags: ArchDaily style, V-Ray, 8k, photorealistic.",
        "标准模式 (MJ/SD)": "Target: General Art. Format: Comma-separated tags.",
        "自然语言 (Google)": "Target: Natural Paragraphs.",
        "二次元 (Niji)": "Target: Anime style.",
        "写实摄影": "Target: Photography 8k.",
        "3D渲染": "Target: 3D Render."
    }
    sys_prompt = base_instruction + mode_rules.get(mode, "")

    # 生成按钮
    if st.button("🚀 生成两种方案", type="primary"):
        current_key = st.session_state.cached_api_key
        if not current_key: st.error("🚨 请先输入密码！"); st.stop()
        
        try:
            client = OpenAI(api_key=current_key, base_url=base_url)
            
            details = []
            if "建筑" in mode:
                if arch_view != "不指定": details.append(f"View: {arch_view}")
                if arch_time != "不指定": details.append(f"Time: {arch_time}")
                if arch_env != "不指定": details.append(f"Env: {arch_env}")
                if arch_style != "不指定": details.append(f"Style: {arch_style}")
                if arch_mat != "不指定": details.append(f"Mat: {arch_mat}")
            else:
                if lighting != "不指定": details.append(f"Light: {lighting}")
                if camera != "不指定": details.append(f"Cam: {camera}")
            
            full_req = f"User Request: {user_input}. Requirements: {', '.join(details)}"

            with st.spinner('AI 正在构思...'):
                resp = client.chat.completions.create(
                    model=text_model,
                    messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": full_req}]
                )
                
                raw = resp.choices[0].message.content
                
                # 解析
                try:
                    p1_cn = raw.split("===PLAN_A_EN===")[0].replace("===PLAN_A_CN===", "").strip()
                    p1_en = raw.split("===PLAN_B_CN===")[0].split("===PLAN_A_EN===")[1].strip()
                    p2_cn = raw.split("===PLAN_B_EN===")[0].split("===PLAN_B_CN===")[1].strip()
                    p2_en = raw.split("===PLAN_B_EN===")[1].strip()
                except:
                    p1_cn, p1_en = "解析失败", raw
                    p2_cn, p2_en = "解析失败", raw

                # 后缀
                suffix = f" {ratio.split(' ')[0]}"
                if "自然语言" not in mode:
                    suffix += f" --s {stylize} --c {chaos}"
                    if negative_prompt: suffix += f" --no {negative_prompt}"
                
                final_p1 = p1_en + suffix
                final_p2 = p2_en + suffix
                
                # 存入 Session State
                st.session_state.last_results = {
                    "p1_cn": p1_cn, "p1_en": final_p1,
                    "p2_cn": p2_cn, "p2_en": final_p2
                }

        except Exception as e:
            st.error(f"出错：{str(e)}")

    # 结果展示与收藏区
    if st.session_state.last_results:
        res = st.session_state.last_results
        
        st.divider()
        c_res1, c_res2 = st.columns(2)
        
        # 方案 A 展示
        with c_res1:
            st.markdown("### 🅰️ 方案 A")
            st.info(res["p1_cn"])
            st.code(res["p1_en"], language="text", wrap_lines=True)
            # 收藏按钮 A
            if st.button("❤️ 收藏方案 A", key="save_btn_a"):
                current_data = load_data()
                new_item = {
                    "category": mode.split(" ")[0],
                    "desc": res["p1_cn"][:20] + "...", 
                    "prompt": res["p1_en"]
                }
                current_data.append(new_item)
                save_data(current_data)
                st.toast("✅ 方案 A 已加入宝库！")

        # 方案 B 展示
        with c_res2:
            st.markdown("### 🅱️ 方案 B")
            st.info(res["p2_cn"])
            st.code(res["p2_en"], language="text", wrap_lines=True)
            # 收藏按钮 B
            if st.button("❤️ 收藏方案 B", key="save_btn_b"):
                current_data = load_data()
                new_item = {
                    "category": mode.split(" ")[0],
                    "desc": res["p2_cn"][:20] + "...", 
                    "prompt": res["p2_en"]
                }
                current_data.append(new_item)
                save_data(current_data)
                st.toast("✅ 方案 B 已加入宝库！")

# ==========================================
# 👉 标签 2：图片反推
# ==========================================
with tab2:
    st.subheader("🖼️ 图片反推")
    uploaded_file = st.file_uploader("拖入图片", type=["jpg", "png"])
    if uploaded_file and st.button("🔍 反推"):
        if not st.session_state.cached_api_key: st.error("请输密码"); st.stop()
        try:
            client = OpenAI(api_key=st.session_state.cached_api_key, base_url=base_url)
            img_b64 = encode_image(uploaded_file)
            with st.spinner('AI 正在看图...'):
                resp = client.chat.completions.create(
                    model=vision_model,
                    messages=[{"role": "user", "content": [{"type": "text", "text": "输出格式：\nCN: [中文]\nEN: [MJ Prompt]"}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}]}]
                )
            raw = resp.choices[0].message.content
            if "EN:" in raw:
                parts = raw.split("EN:")
                cn, en = parts[0].replace("CN:", "").strip(), parts[1].strip()
                st.image(uploaded_file, width=150)
                st.markdown("**中文描述**"); st.info(cn)
                st.markdown("**英文 Prompt**"); st.code(en, language="text", wrap_lines=True)
                
                # 反推结果也能收藏
                if st.button("❤️ 收藏此反推结果"):
                    save_data(load_data() + [{"category": "反推", "desc": "图片反推结果", "prompt": en}])
                    st.toast("✅ 已收藏！")
        except Exception as e: st.error(f"出错：{e}")

# ==========================================
# 👉 标签 3：🌟 我的提示词宝库 (新功能)
# ==========================================
with tab3:
    st.header("🌟 我的提示词宝库")
    
    # 1. 手动添加区
    with st.expander("➕ 手动添加新提示词 (粘贴别人的作业)"):
        with st.form("add_prompt_form"):
            new_cat = st.selectbox("选择分类", ["建筑", "人像", "二次元", "风景", "3D设计", "其他"])
            new_desc = st.text_input("备注名称 (方便查找)", placeholder="例如：极简白色美术馆")
            new_content = st.text_area("提示词内容 (Prompt)", placeholder="粘贴英文提示词在这里...")
            
            if st.form_submit_button("💾 保存到宝库"):
                if new_content:
                    data = load_data()
                    data.append({"category": new_cat, "desc": new_desc, "prompt": new_content})
                    save_data(data)
                    st.success("已保存！")
                    st.rerun()
                else:
                    st.warning("提示词内容不能为空")

    st.divider()

    # 2. 列表展示区
    data = load_data()
    if not data:
        st.info("🗑️ 宝库是空的，快去生成或添加一些吧！")
    else:
        # 筛选器
        all_cats = ["全部"] + list(set([item["category"] for item in data]))
        selected_cat = st.selectbox("📂 按分类筛选", all_cats)
        
        # 倒序显示（最新的在最上面）
        for i, item in enumerate(reversed(data)):
            if selected_cat == "全部" or item["category"] == selected_cat:
                with st.container(border=True):
                    c_info, c_copy, c_del = st.columns([6, 1, 1])
                    
                    with c_info:
                        st.markdown(f"**🏷️ [{item['category']}] {item['desc']}**")
                        st.code(item['prompt'], language="text", wrap_lines=True)
                    
                    with c_del:
                        if st.button("🗑️", key=f"del_{i}", help="删除此条"):
                            # 因为是倒序显示的，所以删除逻辑要处理一下索引
                            real_index = len(data) - 1 - i
                            data.pop(real_index)
                            save_data(data)
                            st.rerun()
