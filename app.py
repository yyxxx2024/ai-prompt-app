import streamlit as st
from openai import OpenAI
import base64
import json
import requests
import time

# 1. 页面设置
st.set_page_config(page_title="🎨 AI 提示词魔法师 Pro", page_icon="🏗️", layout="centered")
st.title("✨ AI 提示词魔法师 Pro")

# --- 🛠️ Gitee 云存储函数 (国内直连版) ---
def get_gitee_config():
    """获取配置信息"""
    return {
        "token": st.secrets["GITEE_TOKEN"],
        "owner": st.secrets["GITEE_OWNER"],
        "repo": st.secrets["GITEE_REPO"],
        "path": st.secrets["GITEE_PATH"]
    }

def load_data():
    """从 Gitee 读取 JSON 数据"""
    cfg = get_gitee_config()
    url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"
    
    try:
        # Gitee API 不需要代理，直接访问
        response = requests.get(url, params={"access_token": cfg['token']})
        if response.status_code == 200:
            content = response.json()['content']
            # Gitee 返回的是 Base64 编码的内容，需要解码
            decoded_str = base64.b64decode(content).decode('utf-8')
            return json.loads(decoded_str)
        else:
            return []
    except Exception:
        return []

def save_data_item(new_item):
    """向 Gitee 追加数据"""
    cfg = get_gitee_config()
    url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"
    
    try:
        # 1. 先获取当前文件内容和 SHA 值 (更新文件必须带 SHA)
        get_res = requests.get(url, params={"access_token": cfg['token']})
        if get_res.status_code != 200:
            st.error("无法连接 Gitee，请检查配置")
            return

        file_info = get_res.json()
        sha = file_info['sha']
        
        # 2. 解析旧数据并追加新数据
        old_content = base64.b64decode(file_info['content']).decode('utf-8')
        data_list = json.loads(old_content)
        data_list.append(new_item)
        
        # 3. 重新编码为 Base64
        new_content_str = json.dumps(data_list, ensure_ascii=False, indent=4)
        new_content_b64 = base64.b64encode(new_content_str.encode('utf-8')).decode('utf-8')
        
        # 4. 推送更新
        payload = {
            "access_token": cfg['token'],
            "content": new_content_b64,
            "sha": sha,
            "message": "Update prompts from Streamlit App"
        }
        put_res = requests.put(url, json=payload)
        
        if put_res.status_code == 200:
            st.toast("☁️ 已同步到 Gitee 云端！")
            time.sleep(1) # 等一秒让 API 反应一下
        else:
            st.error(f"同步失败: {put_res.text}")
            
    except Exception as e:
        st.error(f"云同步出错: {str(e)}")

def delete_data_item(index_to_delete):
    """删除指定数据"""
    cfg = get_gitee_config()
    url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"
    
    try:
        # 1. 获取当前数据
        get_res = requests.get(url, params={"access_token": cfg['token']})
        file_info = get_res.json()
        sha = file_info['sha']
        
        # 2. 删除指定索引
        data_list = json.loads(base64.b64decode(file_info['content']).decode('utf-8'))
        if 0 <= index_to_delete < len(data_list):
            data_list.pop(index_to_delete)
        
        # 3. 编码并推送
        new_content_b64 = base64.b64encode(json.dumps(data_list, ensure_ascii=False, indent=4).encode('utf-8')).decode('utf-8')
        payload = {
            "access_token": cfg['token'],
            "content": new_content_b64,
            "sha": sha,
            "message": "Delete item"
        }
        requests.put(url, json=payload)
        st.toast("🗑️ 删除成功")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"删除失败: {e}")

# --- 🛠️ 辅助函数 ---
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# --- 🔐 身份验证逻辑 ---
if "cached_api_key" not in st.session_state:
    st.session_state.cached_api_key = None
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
tab1, tab2, tab3 = st.tabs(["📝 文本生成 (双方案)", "🖼️ 图片反推", "🌟 云端宝库"])

# ==========================================
# 👉 标签 1：文本生成
# ==========================================
with tab1:
    st.subheader("✍️ 描述画面，生成 2 种方案")
    user_input = st.text_area("你想画什么？", height=100, placeholder="例如：一个坐落在悬崖边的美术馆，扎哈风格...")

    c1, c2 = st.columns(2)
    with c1: ratio = st.selectbox("画幅", ["--ar 16:9", "--ar 4:3", "--ar 3:2", "--ar 9:16", "--ar 1:1"])
    with c2: mode = st.selectbox("模式", ["🏗️ 建筑效果图 (ArchViz)", "标准模式 (MJ/SD)", "自然语言 (Google)", "二次元 (Niji)", "写实摄影", "3D渲染"])

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
        negative_prompt = st.text_input("🚫 负面提示词", value="text, watermark, blurry, low quality, bad anatomy, ugly")

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

    if st.button("🚀 生成两种方案", type="primary"):
        if not st.session_state.cached_api_key: st.error("🚨 请先输入密码！"); st.stop()
        try:
            client = OpenAI(api_key=st.session_state.cached_api_key, base_url=base_url)
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
                resp = client.chat.completions.create(model=text_model, messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": full_req}])
                raw = resp.choices[0].message.content
                try:
                    p1_cn = raw.split("===PLAN_A_EN===")[0].replace("===PLAN_A_CN===", "").strip()
                    p1_en = raw.split("===PLAN_B_CN===")[0].split("===PLAN_A_EN===")[1].strip()
                    p2_cn = raw.split("===PLAN_B_EN===")[0].split("===PLAN_B_CN===")[1].strip()
                    p2_en = raw.split("===PLAN_B_EN===")[1].strip()
                except: p1_cn, p1_en, p2_cn, p2_en = "解析失败", raw, "解析失败", raw
                
                suffix = f" {ratio.split(' ')[0]}"
                if "自然语言" not in mode:
                    suffix += f" --s {stylize} --c {chaos}"
                    if negative_prompt: suffix += f" --no {negative_prompt}"
                
                st.session_state.last_results = {"p1_cn": p1_cn, "p1_en": p1_en + suffix, "p2_cn": p2_cn, "p2_en": p2_en + suffix}
        except Exception as e: st.error(f"出错：{str(e)}")

    if st.session_state.last_results:
        res = st.session_state.last_results
        st.divider()
        c_res1, c_res2 = st.columns(2)
        with c_res1:
            st.markdown("### 🅰️ 方案 A")
            st.info(res["p1_cn"]); st.code(res["p1_en"], language="text", wrap_lines=True)
            if st.button("☁️ 收藏方案 A", key="save_btn_a"):
                save_data_item({"category": mode.split(" ")[0], "desc": res["p1_cn"][:30], "prompt": res["p1_en"]})
        with c_res2:
            st.markdown("### 🅱️ 方案 B")
            st.info(res["p2_cn"]); st.code(res["p2_en"], language="text", wrap_lines=True)
            if st.button("☁️ 收藏方案 B", key="save_btn_b"):
                save_data_item({"category": mode.split(" ")[0], "desc": res["p2_cn"][:30], "prompt": res["p2_en"]})

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
                resp = client.chat.completions.create(model=vision_model, messages=[{"role": "user", "content": [{"type": "text", "text": "输出格式：\nCN: [中文]\nEN: [MJ Prompt]"}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}]}] )
            raw = resp.choices[0].message.content
            if "EN:" in raw:
                cn, en = raw.split("EN:")[0].replace("CN:", "").strip(), raw.split("EN:")[1].strip()
                st.image(uploaded_file, width=150)
                st.info(cn); st.code(en, language="text", wrap_lines=True)
                if st.button("☁️ 收藏此结果"):
                    save_data_item({"category": "反推", "desc": cn[:30], "prompt": en})
        except Exception as e: st.error(f"出错：{e}")

# ==========================================
# 👉 标签 3：🌟 Gitee 云端宝库
# ==========================================
with tab3:
    st.header("🌟 云端提示词宝库 (Gitee同步版)")
    st.caption("数据存储在 Gitee 私有仓库，国内直连，永久保存。")
    
    with st.expander("➕ 手动添加新提示词"):
        with st.form("add_prompt_form"):
            new_cat = st.selectbox("选择分类", ["建筑", "人像", "二次元", "风景", "3D设计", "其他"])
            new_desc = st.text_input("备注名称", placeholder="例如：极简白色美术馆")
            new_content = st.text_area("提示词内容", placeholder="粘贴英文提示词...")
            if st.form_submit_button("💾 保存到云端"):
                if new_content:
                    save_data_item({"category": new_cat, "desc": new_desc, "prompt": new_content})
                    st.rerun()

    st.divider()
    # 尝试加载数据
    try:
        data = load_data()
    except:
        data = []
        
    if not data:
        st.info("🗑️ 宝库是空的 (或者 Secrets 配置有误)")
    else:
        # 筛选与展示
        import pandas as pd
        df = pd.DataFrame(data)
        all_cats = ["全部"] + list(set(d['category'] for d in data))
        selected_cat = st.selectbox("📂 按分类筛选", all_cats)
        
        # 倒序遍历
        for i in range(len(data)-1, -1, -1):
            item = data[i]
            if selected_cat == "全部" or item["category"] == selected_cat:
                with st.container(border=True):
                    c_info, c_del = st.columns([6, 1])
                    with c_info:
                        st.markdown(f"**🏷️ [{item['category']}] {item.get('desc', '无标题')}**")
                        st.code(item['prompt'], language="text", wrap_lines=True)
                    with c_del:
                        if st.button("🗑️", key=f"del_{i}"):
                            delete_data_item(i)
