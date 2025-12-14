import streamlit as st
from openai import OpenAI
import base64
import json
import requests
import time
import io
from docx import Document  # 📦 新增：用于生成 Word

# 1. 页面设置
st.set_page_config(page_title="🎨 AI 提示词魔法师 Pro", page_icon="🏗️", layout="centered")
st.title("✨ AI 提示词魔法师 Pro")

# --- 🛠️ Gitee 云存储函数 ---
def get_gitee_config():
    return {
        "token": st.secrets["GITEE_TOKEN"],
        "owner": st.secrets["GITEE_OWNER"],
        "repo": st.secrets["GITEE_REPO"],
        "path": st.secrets["GITEE_PATH"]
    }

def load_data():
    """从 Gitee 读取数据"""
    cfg = get_gitee_config()
    url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"
    try:
        response = requests.get(url, params={"access_token": cfg['token']})
        if response.status_code == 200:
            content = response.json()['content']
            decoded_str = base64.b64decode(content).decode('utf-8')
            return json.loads(decoded_str)
        return []
    except: return []

def save_data_item(new_item):
    """向 Gitee 追加数据"""
    cfg = get_gitee_config()
    url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"
    try:
        get_res = requests.get(url, params={"access_token": cfg['token']})
        if get_res.status_code != 200: st.error("连接 Gitee 失败"); return

        file_info = get_res.json()
        sha = file_info['sha']
        old_content = base64.b64decode(file_info['content']).decode('utf-8')
        data_list = json.loads(old_content)
        data_list.append(new_item)
        
        new_content_str = json.dumps(data_list, ensure_ascii=False, indent=4)
        new_content_b64 = base64.b64encode(new_content_str.encode('utf-8')).decode('utf-8')
        
        payload = {"access_token": cfg['token'], "content": new_content_b64, "sha": sha, "message": "Add item"}
        requests.put(url, json=payload)
        st.toast("☁️ 已保存到 Gitee！")
        time.sleep(1)
    except Exception as e: st.error(f"同步出错: {e}")

def delete_data_item(index_to_delete):
    """删除数据"""
    cfg = get_gitee_config()
    url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"
    try:
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

# --- 📝 Word 导出函数 (新增) ---
def generate_word_file(data):
    doc = Document()
    doc.add_heading('🌟 我的 AI 提示词宝库', 0)
    
    # 按分类整理数据
    categories = list(set([d['category'] for d in data]))
    categories.sort()
    
    for cat in categories:
        doc.add_heading(f"📂 分类：{cat}", level=1)
        # 获取该分类下的所有提示词
        items = [d for d in data if d['category'] == cat]
        for item in items:
            doc.add_heading(item.get('desc', '无标题'), level=2)
            doc.add_paragraph(f"Prompt:", style='Intense Quote')
            p = doc.add_paragraph(item['prompt'])
            p.runs[0].font.name = 'Courier New' # 设置为等宽字体更好看
            doc.add_paragraph("-" * 20) # 分隔线
            
    # 保存到内存流
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
    manual_key = st.text_input("或手动输入 Key", type="password", label_visibility="collapsed")

    if SYSTEM_PASSWORD and user_password == SYSTEM_PASSWORD:
        if SYSTEM_API_KEY:
            st.session_state.cached_api_key = SYSTEM_API_KEY
            st.success("✅ 令牌已加载")
        else: st.error("Secrets 未配置 API_KEY")
    elif manual_key: st.session_state.cached_api_key = manual_key

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
    with c1: ratio = st.selectbox("画幅", ["--ar 16:9", "--ar 3:4", "--ar 1:1"])
    with c2: mode = st.selectbox("模式", ["🏗️ 建筑效果图", "标准模式", "自然语言", "二次元"])

    with st.expander("🎨 高级参数"):
        if "建筑" in mode:
            ac1, ac2 = st.columns(2)
            with ac1: arch_view = st.selectbox("视角", ["不指定", "人视", "鸟瞰", "透视"])
            with ac2: arch_time = st.selectbox("时刻", ["不指定", "蓝调", "黄金时刻", "日景"])
        else:
            style = st.selectbox("风格", ["不指定", "赛博朋克", "极简", "油画"])

    if st.button("🚀 生成"):
        if not st.session_state.cached_api_key: st.error("请输密码"); st.stop()
        try:
            client = OpenAI(api_key=st.session_state.cached_api_key, base_url=base_url)
            sys_msg = "Generate Plan A (Faithful) and Plan B (Creative). Format:\n===PLAN_A_CN===\n...\n===PLAN_A_EN===\n...\n===PLAN_B_CN===\n...\n===PLAN_B_EN===\n..."
            req_msg = f"Request: {user_input}. Mode: {mode}. Ratio: {ratio}"
            
            with st.spinner('AI 构思中...'):
                resp = client.chat.completions.create(model=text_model, messages=[{"role":"system","content":sys_msg}, {"role":"user","content":req_msg}])
                raw = resp.choices[0].message.content
                try:
                    p1_cn = raw.split("===PLAN_A_EN===")[0].replace("===PLAN_A_CN===", "").strip()
                    p1_en = raw.split("===PLAN_B_CN===")[0].split("===PLAN_A_EN===")[1].strip() + f" {ratio}"
                    p2_cn = raw.split("===PLAN_B_EN===")[0].split("===PLAN_B_CN===")[1].strip()
                    p2_en = raw.split("===PLAN_B_EN===")[1].strip() + f" {ratio}"
                except: p1_cn, p1_en, p2_cn, p2_en = "解析失败", raw, "解析失败", raw
                st.session_state.last_results = {"p1_cn": p1_cn, "p1_en": p1_en, "p2_cn": p2_cn, "p2_en": p2_en}
        except Exception as e: st.error(str(e))

    if st.session_state.last_results:
        res = st.session_state.last_results
        col_a, col_b = st.columns(2)
        with col_a:
            st.info(f"A: {res['p1_cn']}")
            st.code(res['p1_en'])
            # 简化版收藏按钮：默认存到"未分类"
            if st.button("❤️ 存方案 A"): save_data_item({"category": "默认", "desc": res["p1_cn"][:20], "prompt": res["p1_en"]})
        with col_b:
            st.info(f"B: {res['p2_cn']}")
            st.code(res['p2_en'])
            if st.button("❤️ 存方案 B"): save_data_item({"category": "默认", "desc": res["p2_cn"][:20], "prompt": res["p2_en"]})

# ==================== Tab 2: 图片反推 (略) ====================
with tab2:
    st.caption("上传图片反推提示词...")
    # (此处省略部分重复代码以保持精简，功能逻辑同前)
    # ...建议保留之前版本的 Tab 2 代码...
    
# ==================== Tab 3: 云端宝库 (重点更新) ====================
with tab3:
    st.header("🌟 云端提示词宝库")
    
    # 1. 加载数据
    try: data = load_data()
    except: data = []
    
    # 🌟 核心功能 1：Word 导出
    if data:
        col_exp1, col_exp2 = st.columns([3, 1])
        with col_exp1:
            st.caption(f"当前共有 {len(data)} 条收藏数据")
        with col_exp2:
            # 生成 Word 文件流
            docx_file = generate_word_file(data)
            st.download_button(
                label="📥 导出 Word 文档",
                data=docx_file,
                file_name="我的提示词宝库.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    
    st.divider()

    # 🌟 核心功能 2：自定义分类添加
    with st.expander("➕ 手动添加 (支持自定义分类)", expanded=True):
        with st.form("add_prompt_form"):
            # 1. 获取现有分类
            existing_cats = list(set([d['category'] for d in data])) if data else ["建筑", "人像"]
            
            # 2. 交互逻辑：选择现有 OR 新建
            cat_choice = st.selectbox("选择或新建分类", ["📝 手动输入新分类..."] + existing_cats)
            
            # 3. 如果选了手动输入，显示输入框
            custom_cat = ""
            if cat_choice == "📝 手动输入新分类...":
                custom_cat = st.text_input("请输入新分类名称", placeholder="例如：Logo设计")
            
            new_desc = st.text_input("备注名称", placeholder="例如：蓝色科技感Logo")
            new_content = st.text_area("提示词内容", placeholder="粘贴 Prompt...")
            
            if st.form_submit_button("💾 保存到云端"):
                # 确定最终分类名称
                final_cat = custom_cat if cat_choice == "📝 手动输入新分类..." else cat_choice
                
                if not final_cat: st.warning("分类不能为空！"); st.stop()
                if not new_content: st.warning("内容不能为空！"); st.stop()
                
                save_data_item({"category": final_cat, "desc": new_desc, "prompt": new_content})
                st.rerun()

    st.divider()
    
    # 3. 列表展示
    if not data:
        st.info("🗑️ 暂无数据")
    else:
        # 筛选
        all_cats_filter = ["全部"] + list(set(d['category'] for d in data))
        selected_cat_filter = st.selectbox("📂 查看筛选", all_cats_filter)
        
        for i in range(len(data)-1, -1, -1):
            item = data[i]
            if selected_cat_filter == "全部" or item["category"] == selected_cat_filter:
                with st.container(border=True):
                    c1, c2 = st.columns([6, 1])
                    with c1:
                        st.markdown(f"**🏷️ {item['category']} | {item.get('desc','无标题')}**")
                        st.text(item['prompt'])
                    with c2:
                        if st.button("🗑️", key=f"del_{i}"): delete_data_item(i)
