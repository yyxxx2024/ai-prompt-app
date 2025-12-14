import streamlit as st
from openai import OpenAI
import base64
import json
import requests
import time
import io
from docx import Document

# 1. 页面设置
st.set_page_config(page_title="🎨 AI 提示词魔法师 Pro", page_icon="🏗️", layout="centered")
st.title("✨ AI 提示词魔法师 Pro")

# --- 🛠️ Gitee 云存储配置 ---
def get_gitee_config():
    return {
        "token": st.secrets["GITEE_TOKEN"],
        "owner": st.secrets["GITEE_OWNER"],
        "repo": st.secrets["GITEE_REPO"],
        "path": st.secrets["GITEE_PATH"]
    }

def load_data():
    """从 Gitee 读取数据"""
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"
        response = requests.get(url, params={"access_token": cfg['token']})
        if response.status_code == 200:
            content = response.json()['content']
            decoded_str = base64.b64decode(content).decode('utf-8')
            return json.loads(decoded_str)
        return []
    except: return []

def save_data_item(new_item):
    """向 Gitee 追加数据"""
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"
        
        # 1. 获取旧数据
        get_res = requests.get(url, params={"access_token": cfg['token']})
        if get_res.status_code != 200: 
            st.error("Gitee 连接失败，请检查 Secrets 配置")
            return

        file_info = get_res.json()
        sha = file_info['sha']
        
        # 解析旧内容
        try:
            old_content = base64.b64decode(file_info['content']).decode('utf-8')
            if not old_content: data_list = []
            else: data_list = json.loads(old_content)
        except: data_list = []
        
        # 追加新内容
        data_list.append(new_item)
        
        # 2. 推送新数据
        new_content_str = json.dumps(data_list, ensure_ascii=False, indent=4)
        new_content_b64 = base64.b64encode(new_content_str.encode('utf-8')).decode('utf-8')
        
        payload = {
            "access_token": cfg['token'], 
            "content": new_content_b64, 
            "sha": sha, 
            "message": "Add item from Streamlit"
        }
        
        put_res = requests.put(url, json=payload)
        if put_res.status_code == 200:
            st.toast("☁️ 已保存到 Gitee 云端！")
            time.sleep(1)
        else:
            st.error(f"保存失败: {put_res.text}")
            
    except Exception as e: 
        st.error(f"同步出错: {e}")

def delete_data_item(index_to_delete):
    """删除数据"""
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"
        
        get_res = requests.get(url, params={"access_token": cfg['token']})
        file_info = get_res.json()
        sha = file_info['sha']
        data_list = json.loads(base64.b64decode(file_info['content']).decode('utf-8'))
        
        if 0 <= index_to_delete < len(data_list):
            data_list.pop(index_to_delete)
        
        new_content_b64 = base64.b64encode(json.dumps(data_list, ensure_ascii=False, indent=4).encode('utf-8')).decode('utf-8')
        payload = {"access_token": cfg['token'], "content": new_content_b64, "sha": sha, "message": "Delete item"}
        requests.put(url, json=payload)
        st.toast("🗑️ 删除成功")
        time.sleep(1)
        st.rerun()
    except Exception as e: st.error(f"删除失败: {e}")

# --- 📝 Word 导出函数 ---
def generate_word_file(data):
    doc = Document()
    doc.add_heading('🌟 我的 AI 提示词宝库', 0)
    categories = list(set([d['category'] for d in data]))
    categories.sort()
    for cat in categories:
        doc.add_heading(f"📂 分类：{cat}", level=1)
        items = [d for d in data if d['category'] == cat]
        for item in items:
            doc.add_heading(item.get('desc', '无标题'), level=2)
            p = doc.add_paragraph(item['prompt'])
            doc.add_paragraph("-" * 20)
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- 🛠️ 辅助函数 ---
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# --- 🔐 身份验证 ---
if "cached_api_key" not in st.session_state: st.session_state.cached_api_key = None
if "last_results" not in st.session_state: st.session_state.last_results = None

with st.sidebar:
    st.header("🔐 身份验证")
    SYSTEM_PASSWORD = st.secrets.get("APP_PASSWORD", None)
    SYSTEM_API_KEY = st.secrets.get("API_KEY", None)
    user_password = st.text_input("🔑 访问密码", type="password", placeholder="输入密码...")
    
    if SYSTEM_PASSWORD and user_password == SYSTEM_PASSWORD:
        if SYSTEM_API_KEY:
            st.session_state.cached_api_key = SYSTEM_API_KEY
            st.success("✅ 令牌已加载")
        else: st.error("Secrets 未配置 API_KEY")

    st.markdown("---")
    st.header("⚙️ API 设置")
    base_url = st.text_input("API 地址", value="https://hk-api.gptbest.vip/v1")
    text_model = st.text_input("Text Model", value="deepseek-chat", label_visibility="collapsed")
    vision_model = st.text_input("Vision Model", value="gpt-4o-mini", label_visibility="collapsed")

# --- 🏗️ 标签页 ---
tab1, tab2, tab3 = st.tabs(["📝 文本生成", "🖼️ 图片反推", "🌟 云端宝库"])

# ==================== Tab 1: 文本生成 ====================
with tab1:
    st.subheader("✍️ 双方案生成")
    user_input = st.text_area("画面描述", height=80, placeholder="例如：极简白色美术馆...")
    c1, c2 = st.columns(2)
    with c1: ratio = st.selectbox("画幅", ["--ar 16:9", "--ar 3:4", "--ar 1:1", "--ar 9:16"])
    with c2: mode = st.selectbox("模式", ["🏗️ 建筑效果图", "标准模式", "自然语言", "二次元"])

    with st.expander("🎨 高级参数"):
        if "建筑" in mode:
            ac1, ac2 = st.columns(2)
            with ac1: arch_view = st.selectbox("视角", ["不指定", "人视", "鸟瞰", "透视"])
            with ac2: arch_time = st.selectbox("时刻", ["不指定", "蓝调", "黄金时刻", "日景"])
        else:
            col_a, col_b = st.columns(2)
            with col_a: lighting = st.selectbox("光线", ["不指定", "自然光", "电影光", "霓虹"])
            with col_b: mood = st.selectbox("氛围", ["不指定", "梦幻", "史诗", "阴郁"])

    if st.button("🚀 生成"):
        if not st.session_state.cached_api_key: st.error("请输密码"); st.stop()
        try:
            client = OpenAI(api_key=st.session_state.cached_api_key, base_url=base_url)
            sys_msg = "Generate Plan A (Faithful) and Plan B (Creative). Format:\n===PLAN_A_CN===\n...\n===PLAN_A_EN===\n...\n===PLAN_B_CN===\n...\n===PLAN_B_EN===\n..."
            req_msg = f"Request: {user_input}. Mode: {mode}. Ratio: {ratio}"
            
            with st.spinner('AI 构思中...'):
                resp = client.chat.completions.create(model=text_model, messages=[{"role":"system","content":sys_msg}, {"role":"user","content":req_msg}])
                raw = resp.choices[0].message.content
                # 修复了这里的 try/except 结构
                try:
                    p1_cn = raw.split("===PLAN_A_EN===")[0].replace("===PLAN_A_CN===", "").strip()
                    p1_en = raw.split("===PLAN_B_CN===")[0].split("===PLAN_A_EN===")[1].strip() + f" {ratio}"
                    p2_cn = raw.split("===PLAN_B_EN===")[0].split("===PLAN_B_CN===")[1].strip()
                    p2_en = raw.split("===PLAN_B_EN===")[1].strip() + f" {ratio}"
                except: 
                    p1_cn, p1_en, p2_cn, p2_en = "解析失败", raw, "解析失败", raw
                
                st.session_state.last_results = {"p1_cn": p1_cn, "p1_en": p1_en, "p2_cn": p2_cn, "p2_en": p2_en}
        except Exception as e: st.error(str(e))

    if st.session_state.last_results:
        res = st.session_state.last_results
        col_a, col_b = st.columns(2)
        with col_a:
            st.info(f"A: {res['p1_cn']}")
            st.code(res['p1_en'])
            if st.button("❤️ 存方案 A"): save_data_item({"category": "默认", "desc": res["p1_cn"][:20], "prompt": res["p1_en"]})
        with col_b:
            st.info(f"B: {res['p2_cn']}")
            st.code(res['p2_en'])
            if st.button("❤️ 存方案 B"): save_data_item({"category": "默认", "desc": res["p2_cn"][:20], "prompt": res["p2_en"]})

# ==================== Tab 2: 图片反推 ====================
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
                st.info(cn); st.code(en)
                if st.button("❤️ 收藏此结果"): save_data_item({"category": "反推", "desc": cn[:20], "prompt": en})
        except Exception as e: st.error(str(e))

# ==================== Tab 3: 云端宝库 ====================
with tab3:
    st.header("🌟 云端宝库 (Gitee版)")
    try: data = load_data()
    except: data = []
    
    if data:
        docx = generate_word_file(data)
        st.download_button("📥 导出 Word", data=docx, file_name="提示词库.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    st.divider()
    with st.expander("➕ 手动添加 (支持新建分类)", expanded=True):
        with st.form("add_form"):
            cats = list(set([d['category'] for d in data])) if data else ["建筑", "人像"]
            cat_mode = st.selectbox("分类", ["📝 新建分类..."] + cats)
            custom_cat = ""
            if cat_mode == "📝 新建分类...": custom_cat = st.text_input("输入新分类名")
            
            desc = st.text_input("备注")
            content = st.text_area("内容")
            if st.form_submit_button("💾 保存"):
                final_cat = custom_cat if cat_mode == "📝 新建分类..." else cat_mode
                if final_cat and content:
                    save_data_item({"category": final_cat, "desc": desc, "prompt": content})
                    st.rerun()

    st.divider()
    if not data: st.info("暂无数据 (请检查 Secrets 配置)")
    else:
        all_cats = ["全部"] + list(set([d['category'] for d in data]))
        sel_cat = st.selectbox("筛选", all_cats)
        for i in range(len(data)-1, -1, -1):
            d = data[i]
            if sel_cat == "全部" or d['category'] == sel_cat:
                with st.container(border=True):
                    c1, c2 = st.columns([6,1])
                    with c1: st.markdown(f"**[{d['category']}] {d.get('desc','')}**"); st.text(d['prompt'])
                    with c2: 
                        if st.button("🗑️", key=f"d_{i}"): delete_data_item(i)
