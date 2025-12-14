import streamlit as st
from openai import OpenAI
import base64
import json
import requests
import time
import io
# 尝试导入 docx
try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# ================= 1. 页面基本设置 =================
st.set_page_config(page_title="Neo-Prompt AI", page_icon="🤖", layout="centered")

# ================= 🎨 核心：注入赛博朋克 CSS 样式 =================
def add_cyberpunk_style():
    st.markdown("""
    <style>
        /* 1. 全局背景：深空渐变 */
        .stApp {
            background: linear-gradient(135deg, #050511 0%, #1a1a2e 50%, #16213e 100%);
            background-attachment: fixed;
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }

        /* 2. 主容器：玻璃拟态效果 */
        .block-container {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid rgba(0, 255, 255, 0.1);
            padding: 30px;
            box-shadow: 0 0 40px rgba(0, 0, 0, 0.5);
            max-width: 800px;
        }

        /* 3. 标题样式：霓虹发光文字 */
        h1 {
            color: #fff;
            text-align: center;
            text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff;
            font-weight: 800 !important;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        h2, h3 {
            color: #e0e0e0 !important;
            border-bottom: 1px solid rgba(0, 255, 255, 0.3);
            padding-bottom: 10px;
        }

        /* 4. 输入框 (Text Area & Input)：深色背景 + 青色边框 */
        .stTextArea textarea, .stTextInput input {
            background-color: rgba(0, 0, 0, 0.4) !important;
            color: #00ffff !important; /* 霓虹青字体 */
            border: 1px solid rgba(0, 255, 255, 0.3) !important;
            border-radius: 12px;
            transition: all 0.3s ease;
        }
        .stTextArea textarea:focus, .stTextInput input:focus {
            border-color: #00ffff !important;
            box-shadow: 0 0 15px rgba(0, 255, 255, 0.4);
        }

        /* 5. 下拉菜单 (Selectbox) */
        .stSelectbox div[data-baseweb="select"] > div {
            background-color: rgba(0, 0, 0, 0.4) !important;
            color: #fff !important;
            border: 1px solid rgba(255, 0, 255, 0.3); /* 粉色边框 */
            border-radius: 10px;
        }

        /* 6. 按钮 (Button)：橙色/粉色渐变霓虹灯 */
        div.stButton > button {
            width: 100%;
            background: linear-gradient(90deg, #ff4b1f, #ff9068); /* 橙红渐变 */
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 30px;
            font-size: 18px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 0 20px rgba(255, 75, 31, 0.4);
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 30px rgba(255, 75, 31, 0.7);
            background: linear-gradient(90deg, #ff9068, #ff4b1f);
        }
        
        /* 次级按钮 (收藏/删除) 改为青色风格 */
        div.stButton > button:not([kind="primary"]) {
             background: transparent;
             border: 1px solid #00ffff;
             color: #00ffff;
             box-shadow: none;
        }
        div.stButton > button:not([kind="primary"]):hover {
             background: rgba(0, 255, 255, 0.1);
             box-shadow: 0 0 10px #00ffff;
        }

        /* 7. 侧边栏 (Sidebar) */
        section[data-testid="stSidebar"] {
            background-color: #0a0a12;
            border-right: 1px solid #333;
        }
        
        /* 8. 标签页 (Tabs) */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            color: #aaa;
            border: none;
        }
        .stTabs [aria-selected="true"] {
            background-color: rgba(0, 255, 255, 0.1) !important;
            color: #00ffff !important;
            border: 1px solid #00ffff !important;
            box-shadow: 0 0 10px rgba(0, 255, 255, 0.2);
        }

        /* 9. 代码块结果显示 */
        code {
            color: #ff00ff !important; /* 霓虹粉代码 */
            font-family: 'Courier New', monospace;
        }
        .stCode {
            background-color: #000 !important;
            border: 1px solid #333;
            border-radius: 10px;
        }
        
        /* 10. 提示框 (Success/Info/Error) */
        .stAlert {
            background-color: rgba(0,0,0,0.6);
            backdrop-filter: blur(5px);
            border: 1px solid #555;
            color: #fff;
        }
    </style>
    """, unsafe_allow_html=True)

add_cyberpunk_style()

# ================= 🛠️ 工具函数区 (保持逻辑不变) =================

def get_gitee_config():
    return {
        "token": st.secrets.get("GITEE_TOKEN", ""),
        "owner": st.secrets.get("GITEE_OWNER", ""),
        "repo": st.secrets.get("GITEE_REPO", ""),
        "path": st.secrets.get("GITEE_PATH", "")
    }

def load_data():
    try:
        cfg = get_gitee_config()
        if not cfg["token"]: return []
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"
        res = requests.get(url, params={"access_token": cfg['token']})
        if res.status_code == 200:
            content = res.json()['content']
            decoded = base64.b64decode(content).decode('utf-8')
            return json.loads(decoded)
        return []
    except: return []

def save_data_item(new_item):
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"
        res = requests.get(url, params={"access_token": cfg['token']})
        if res.status_code != 200:
            st.error("Gitee 连接失败")
            return
        file_info = res.json()
        sha = file_info['sha']
        try:
            old_text = base64.b64decode(file_info['content']).decode('utf-8')
            data_list = json.loads(old_text)
        except: data_list = []
        data_list.append(new_item)
        new_text = json.dumps(data_list, ensure_ascii=False, indent=4)
        new_b64 = base64.b64encode(new_text.encode('utf-8')).decode('utf-8')
        payload = {"access_token": cfg['token'], "content": new_b64, "sha": sha, "message": "Add item"}
        requests.put(url, json=payload)
        st.toast("✅ 已同步到云端！")
        time.sleep(1)
    except Exception as e: st.error(f"保存出错: {e}")

def delete_data_item(index):
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"
        res = requests.get(url, params={"access_token": cfg['token']})
        file_info = res.json()
        sha = file_info['sha']
        data_list = json.loads(base64.b64decode(file_info['content']).decode('utf-8'))
        if 0 <= index < len(data_list): data_list.pop(index)
        new_b64 = base64.b64encode(json.dumps(data_list, ensure_ascii=False, indent=4).encode('utf-8')).decode('utf-8')
        requests.put(url, json={"access_token": cfg['token'], "content": new_b64, "sha": sha, "message": "Delete"})
        st.toast("🗑️ 删除成功")
        time.sleep(1)
        st.rerun()
    except Exception as e: st.error(f"删除失败: {e}")

def generate_word(data):
    if not HAS_DOCX: return None
    doc = Document()
    doc.add_heading('🌟 我的 AI 提示词宝库', 0)
    cats = sorted(list(set([d['category'] for d in data])))
    for cat in cats:
        doc.add_heading(f"📂 {cat}", level=1)
        items = [d for d in data if d['category'] == cat]
        for item in items:
            doc.add_heading(item.get('desc', '无标题'), level=2)
            doc.add_paragraph(item['prompt'])
            doc.add_paragraph("-" * 30)
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def encode_image(file):
    return base64.b64encode(file.getvalue()).decode('utf-8')

# ================= 🔐 侧边栏 =================
if "cached_api_key" not in st.session_state: st.session_state.cached_api_key = None
if "last_results" not in st.session_state: st.session_state.last_results = None

with st.sidebar:
    st.markdown("### 🔐 身份验证")
    sys_pass = st.secrets.get("APP_PASSWORD", "")
    sys_key = st.secrets.get("API_KEY", "")
    user_pass = st.text_input("访问密码", type="password")
    
    if user_pass and user_pass == sys_pass:
        st.session_state.cached_api_key = sys_key
        st.success("✅ 验证通过")
    elif user_pass:
        st.error("❌ 密码错误")

    st.markdown("---")
    st.markdown("### ⚙️ 系统设置")
    base_url = st.text_input("API 地址", value="https://hk-api.gptbest.vip/v1")
    text_model = st.text_input("文本模型", value="deepseek-chat")
    vision_model = st.text_input("视觉模型", value="gpt-4o-mini")

# ================= 🏗️ 主界面 =================
st.markdown("<h1>NEO-PROMPT AI <small>v2.0</small></h1>", unsafe_allow_html=True)
st.caption("🚀 Cyberpunk Style Enabled | Powered by DeepSeek & GPT-4o")

tab1, tab2, tab3 = st.tabs(["📝 生成提示词", "🖼️ 图片反推", "🌟 云端宝库"])

# --- Tab 1 ---
with tab1:
    user_input = st.text_area("输入你的创意概念...", height=100, placeholder="例如：一座漂浮在云端的赛博朋克城市，霓虹灯闪烁...")
    
    c1, c2 = st.columns(2)
    with c1: ratio = st.selectbox("画幅比例", ["--ar 16:9", "--ar 3:4", "--ar 1:1", "--ar 9:16"])
    with c2: mode = st.selectbox("生成模式", ["🏗️ 建筑效果图", "标准模式", "自然语言", "二次元"])

    with st.expander("🎨 高级参数配置 (点击展开)"):
        st.caption("根据模式选择参数：")
        if "建筑" in mode:
            ac1, ac2 = st.columns(2)
            with ac1: arch_view = st.selectbox("视角", ["不指定", "人视", "鸟瞰", "透视"])
            with ac2: arch_time = st.selectbox("时刻", ["不指定", "蓝调", "黄金时刻", "日景"])
        if "建筑" not in mode:
            col_a, col_b = st.columns(2)
            with col_a: lighting = st.selectbox("光线", ["不指定", "自然光", "电影光", "霓虹"])
            with col_b: mood = st.selectbox("氛围", ["不指定", "梦幻", "史诗", "阴郁"])

    # 这里的按钮会自动应用 CSS 里的发光样式
    if st.button("GENERATE / 生成双方案", type="primary"):
        if not st.session_state.cached_api_key:
            st.error("请先在侧边栏输入密码解锁！")
            st.stop()
            
        try:
            client = OpenAI(api_key=st.session_state.cached_api_key, base_url=base_url)
            sys_msg = """
            Generate Plan A (Faithful) and Plan B (Creative). 
            Format exactly like this:
            ===PLAN_A_CN===
            [Chinese A]
            ===PLAN_A_EN===
            [English A]
            ===PLAN_B_CN===
            [Chinese B]
            ===PLAN_B_EN===
            [English B]
            """
            req_msg = f"User Request: {user_input}. Mode: {mode}. Ratio: {ratio}"
            
            with st.spinner('AI 正在连接矩阵网络...'):
                resp = client.chat.completions.create(model=text_model, messages=[{"role":"system","content":sys_msg}, {"role":"user","content":req_msg}])
                raw = resp.choices[0].message.content
                try:
                    p1_cn = raw.split("===PLAN_A_EN===")[0].replace("===PLAN_A_CN===", "").strip()
                    p1_en = raw.split("===PLAN_B_CN===")[0].split("===PLAN_A_EN===")[1].strip() + f" {ratio}"
                    p2_cn = raw.split("===PLAN_B_EN===")[0].split("===PLAN_B_CN===")[1].strip()
                    p2_en = raw.split("===PLAN_B_EN===")[1].strip() + f" {ratio}"
                except:
                    p1_cn, p1_en, p2_cn, p2_en = "解析失败", raw, "解析失败", raw
                
                st.session_state.last_results = {"p1_cn": p1_cn, "p1_en": p1_en, "p2_cn": p2_cn, "p2_en": p2_en}
        except Exception as e: st.error(f"API Error: {e}")

    if st.session_state.last_results:
        res = st.session_state.last_results
        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("### PROMPT 1: 精准版")
            st.info(res['p1_cn'])
            st.code(res['p1_en'])
            if st.button("💾 收藏方案 A"):
                save_data_item({"category": "默认", "desc": res["p1_cn"][:20], "prompt": res["p1_en"]})
        with col_b:
            st.markdown("### PROMPT 2: 创意版")
            st.info(res['p2_cn'])
            st.code(res['p2_en'])
            if st.button("💾 收藏方案 B"):
                save_data_item({"category": "默认", "desc": res["p2_cn"][:20], "prompt": res["p2_en"]})

# --- Tab 2 ---
with tab2:
    up_file = st.file_uploader("上传图片 (Image Upload)", type=["jpg", "png"])
    if up_file and st.button("ANALYZE / 开始反推"):
        if not st.session_state.cached_api_key: st.error("请先输入密码"); st.stop()
        try:
            client = OpenAI(api_key=st.session_state.cached_api_key, base_url=base_url)
            b64 = encode_image(up_file)
            with st.spinner('Scanning Image...'):
                resp = client.chat.completions.create(model=vision_model, messages=[{"role":"user","content":[{"type":"text","text":"输出格式：\nCN: [中文描述]\nEN: [MJ Prompt]"},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}] )
            raw = resp.choices[0].message.content
            if "EN:" in raw:
                cn, en = raw.split("EN:")[0].replace("CN:", "").strip(), raw.split("EN:")[1].strip()
                st.image(up_file, width=200)
                st.info(cn); st.code(en)
                if st.button("💾 收藏此结果"): save_data_item({"category": "反推", "desc": cn[:20], "prompt": en})
        except Exception as e: st.error(str(e))

# --- Tab 3 ---
with tab3:
    data = load_data()
    if data and HAS_DOCX:
        docx = generate_word(data)
        st.download_button("📥 导出 Word 文档", data=docx, file_name="NeoPrompts.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    elif not HAS_DOCX: st.warning("缺少 python-docx 库")

    st.divider()
    with st.expander("➕ 添加新数据"):
        with st.form("add_new"):
            cats = sorted(list(set([d['category'] for d in data]))) if data else ["建筑", "人像"]
            c_mode = st.selectbox("分类", ["📝 新建..."] + cats)
            new_c = st.text_input("输入新分类名") if c_mode == "📝 新建..." else c_mode
            desc = st.text_input("备注")
            cont = st.text_area("内容")
            if st.form_submit_button("保存"):
                save_data_item({"category": new_c, "desc": desc, "prompt": cont})
                st.rerun()
    
    st.divider()
    if not data: st.info("云端数据库为空")
    else:
        f_cat = st.selectbox("筛选分类", ["全部"] + sorted(list(set([d['category'] for d in data]))))
        for i in range(len(data)-1, -1, -1):
            d = data[i]
            if f_cat == "全部" or d['category'] == f_cat:
                with st.container(border=True):
                    c1, c2 = st.columns([6,1])
                    with c1: st.markdown(f"**[{d['category']}] {d.get('desc','')}**"); st.text(d['prompt'])
                    with c2: 
                        if st.button("🗑️", key=f"del_{i}"): delete_data_item(i)
