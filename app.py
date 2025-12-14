import streamlit as st
from openai import OpenAI
import base64
import json
import requests
import time
import io
import hashlib
import qrcode
from io import BytesIO

# 尝试导入 docx
try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# ================= 1. 页面基本设置 =================
st.set_page_config(page_title="AI 提示词魔法师 Pro", page_icon="🍊", layout="centered")

# ================= 🎨 UI 样式 =================
def add_modern_light_style():
    st.markdown("""
    <style>
        .stApp { background-color: #f7f9fb; font-family: 'PingFang SC', sans-serif; color: #2c3e50; }
        .block-container { background-color: #ffffff; border-radius: 12px; padding: 3rem 2rem; box-shadow: 0 4px 20px rgba(0,0,0,0.06); max-width: 850px; }
        h1 { color: #1a1a1a; font-weight: 700 !important; letter-spacing: -1px; }
        .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
            background-color: #f8f9fa !important; border: 1px solid #e9ecef !important; border-radius: 8px; color: #495057 !important;
        }
        .stTextArea textarea:focus, .stTextInput input:focus { border-color: #ff8c42 !important; box-shadow: 0 0 0 2px rgba(255, 140, 66, 0.2); }
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #ff9a44 0%, #fc6076 100%); border: none; color: white !important;
            padding: 12px 28px; border-radius: 8px; font-weight: 600; font-size: 16px; width: 100%; transition: all 0.3s;
            box-shadow: 0 4px 12px rgba(252, 96, 118, 0.3);
        }
        div.stButton > button[kind="primary"]:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(252, 96, 118, 0.4); }
        div.stButton > button[kind="secondary"] { border: 1px solid #eee; color: #666; background-color: white; border-radius: 6px; }
        div.stButton > button[kind="secondary"]:hover { border-color: #ff9a44; color: #ff9a44; background-color: #fff8f0; }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [aria-selected="true"] { color: #fc6076 !important; border-bottom-color: #fc6076 !important; }
        .stCode { background-color: #f8f9fa !important; border: 1px solid #eee; border-radius: 8px; }
        .stInfo { background-color: #f0f7ff; color: #0052cc; border: none; border-radius: 8px; }
        .stSuccess { background-color: #e6fffa; color: #009975; border: none; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

add_modern_light_style()

# ================= 🛠️ Gitee 核心函数 =================

def get_gitee_config():
    return {
        "token": st.secrets.get("GITEE_TOKEN", ""),
        "owner": st.secrets.get("GITEE_OWNER", ""),
        "repo": st.secrets.get("GITEE_REPO", "")
    }

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_all_users():
    """获取所有用户 (带自动纠错功能)"""
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/users.json"
        res = requests.get(url, params={"access_token": cfg['token']})
        
        if res.status_code == 200:
            content = res.json()['content']
            decoded = base64.b64decode(content).decode('utf-8')
            data = json.loads(decoded)
            
            # 🛠️【核心修复】如果不小心存成了列表[]，强制转为字典{}
            if isinstance(data, list):
                return {} 
            return data
            
        elif res.status_code == 404:
            return {} 
        return {}
    except: return {}

def register_new_user(username, password):
    users = get_all_users()
    
    # 再次确保 users 是字典
    if isinstance(users, list): users = {}

    if username in users:
        return False, "❌ 用户名已存在"
    
    users[username] = hash_password(password)
    
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/users.json"
        
        # 获取 sha 用于更新
        sha = None
        get_res = requests.get(url, params={"access_token": cfg['token']})
        if get_res.status_code == 200:
            sha = get_res.json()['sha']
        
        # 编码字典为JSON
        new_text = json.dumps(users, ensure_ascii=False, indent=4)
        new_b64 = base64.b64encode(new_text.encode('utf-8')).decode('utf-8')
        
        payload = {
            "access_token": cfg['token'],
            "content": new_b64,
            "message": f"Register user {username}"
        }
        if sha: payload["sha"] = sha
        
        res = requests.put(url, json=payload)
        
        if res.status_code in [200, 201]:
            return True, "✅ 注册成功！已自动登录"
        else:
            return False, f"注册失败: {res.text}"
    except Exception as e:
        return False, str(e)

# --- 数据存储系统 ---

def get_user_filename(username):
    return f"prompts_{username}.json"

def load_data(username):
    try:
        cfg = get_gitee_config()
        if not cfg["token"]: return []
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{get_user_filename(username)}"
        res = requests.get(url, params={"access_token": cfg['token']})
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
        return []
    except: return []

def save_data_item(new_item, username):
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{get_user_filename(username)}"
        res = requests.get(url, params={"access_token": cfg['token']})
        sha, data_list = None, []
        if res.status_code == 200:
            sha = res.json()['sha']
            try: data_list = json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
            except: pass
        data_list.append(new_item)
        new_b64 = base64.b64encode(json.dumps(data_list, ensure_ascii=False, indent=4).encode('utf-8')).decode('utf-8')
        payload = {"access_token": cfg['token'], "content": new_b64, "message": f"Add by {username}"}
        if sha: payload["sha"] = sha
        requests.put(url, json=payload)
        st.toast(f"✅ 已保存到 {username} 的宝库")
        time.sleep(1)
    except Exception as e: st.error(f"保存出错: {e}")

def delete_data_item(index, username):
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{get_user_filename(username)}"
        res = requests.get(url, params={"access_token": cfg['token']})
        if res.status_code == 200:
            info = res.json()
            data = json.loads(base64.b64decode(info['content']).decode('utf-8'))
            if 0 <= index < len(data):
                data.pop(index)
                new_b64 = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8')).decode('utf-8')
                requests.put(url, json={"access_token": cfg['token'], "content": new_b64, "sha": info['sha'], "message": "Del"})
                st.toast("🗑️ 删除成功")
                time.sleep(1)
                st.rerun()
    except: pass

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
            doc.add_paragraph(item['prompt']); doc.add_paragraph("-" * 30)
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def encode_image(file): return base64.b64encode(file.getvalue()).decode('utf-8')

def custom_select(label, options, key_suffix):
    selected = st.selectbox(label, ["不指定"] + options + ["📝 自定义输入..."], key=f"sel_{key_suffix}")
    if selected == "📝 自定义输入...":
        val = st.text_input(f"请输入 {label}", key=f"txt_{key_suffix}")
        return val if val else "不指定"
    return selected

def generate_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

# ================= 🚀 初始化 =================
if "current_user" not in st.session_state: st.session_state.current_user = None
if "last_results" not in st.session_state: st.session_state.last_results = None

# URL 自动登录逻辑
if not st.session_state.current_user:
    params = st.query_params
    if "u" in params and "p" in params:
        u_arg = params["u"]
        p_arg = params["p"]
        users_db = get_all_users()
        try:
            decoded_p = base64.b64decode(p_arg).decode('utf-8')
            hashed_p = hash_password(decoded_p)
            if u_arg in users_db and users_db[u_arg] == hashed_p:
                st.session_state.current_user = u_arg
                st.toast(f"🎉 扫码登录成功！欢迎 {u_arg}")
        except: pass

# ================= 🔐 侧边栏 =================
with st.sidebar:
    st.markdown("### 🔐 账户中心")
    
    if st.session_state.current_user:
        st.success(f"👤 已登录: **{st.session_state.current_user}**")
        
        with st.expander("📱 生成免密二维码"):
            st.caption("朋友扫此码可直接登录你的账号")
            try:
                confirm_pass = st.text_input("验证当前密码生成", type="password")
                if confirm_pass:
                    users_db = get_all_users()
                    if users_db.get(st.session_state.current_user) == hash_password(confirm_pass):
                        b64_pass = base64.b64encode(confirm_pass.encode()).decode()
                        app_url = "https://share.streamlit.io" # 这里可以换成你具体的app地址
                        login_link = f"{app_url}?u={st.session_state.current_user}&p={b64_pass}"
                        qr_img = generate_qr_code(login_link)
                        st.image(qr_img, caption="微信扫一扫，免密直连")
                    else: st.error("密码错误")
            except: pass

        if st.button("退出登录"):
            st.session_state.current_user = None
            st.rerun()
    else:
        auth_mode = st.radio("选择模式", ["登录", "注册新账号"], horizontal=True)
        user_input_name = st.text_input("用户名", placeholder="设置英文用户名")
        user_input_pass = st.text_input("密码", type="password")
        
        if auth_mode == "登录":
            if st.button("登录", type="primary"):
                users_db = get_all_users()
                hashed_pw = hash_password(user_input_pass)
                if user_input_name in users_db and users_db[user_input_name] == hashed_pw:
                    st.session_state.current_user = user_input_name
                    st.success("✅ 登录成功！")
                    time.sleep(0.5)
                    st.rerun()
                else: st.error("❌ 用户名或密码错误")
        else:
            if st.button("✨ 立即注册"):
                if len(user_input_name) < 3: st.warning("用户名太短")
                elif not user_input_pass: st.warning("密码不能为空")
                else:
                    success, msg = register_new_user(user_input_name, user_input_pass)
                    if success:
                        st.session_state.current_user = user_input_name
                        st.success(msg)
                        time.sleep(1)
                        st.rerun()
                    else: st.error(msg)

    st.markdown("---")
    st.markdown("### ⚙️ 系统设置")
    base_url = st.text_input("API 地址", value="https://hk-api.gptbest.vip/v1")
    text_model = st.text_input("文本模型", value="deepseek-chat")
    vision_model = st.text_input("视觉模型", value="gpt-4o-mini")

# ================= 🏗️ 主界面 =================
st.markdown("# 🍊 AI Prompt Wizard <small>Pro</small>", unsafe_allow_html=True)

if not st.session_state.current_user:
    st.info("👋 欢迎！请在左侧 **登录** 或 **注册**。")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📝 生成提示词", "🖼️ 图片反推", "🌟 我的云端宝库"])

# --- Tab 1 ---
with tab1:
    user_input = st.text_area("输入", height=100, label_visibility="collapsed", placeholder="例如：一个极简风格的白色美术馆...")
    c1, c2 = st.columns(2)
    with c1: ratio = st.selectbox("画幅", ["--ar 16:9", "--ar 3:4", "--ar 1:1", "--ar 9:16"])
    with c2: mode = st.selectbox("模式", ["🏗️ 建筑效果图 (ArchViz)", "📐 建筑设计 (Design Concept)", "标准模式 (MJ/SD)", "自然语言 (Google)", "二次元 (Niji)", "写实摄影"])

    with st.expander("🎨 高级参数配置 (支持自定义)", expanded=True):
        if "效果图" in mode:
            st.caption("🏗️ **效果图参数**")
            ac1, ac2, ac3 = st.columns(3)
            with ac1: viz_view = custom_select("视点", ["人视", "半鸟瞰", "顶视", "虫视"], "v1")
            with ac2: viz_time = custom_select("时刻", ["黄金时刻", "蓝调", "正午", "阴天", "雨夜"], "v2")
            with ac3: viz_env = custom_select("环境", ["街道", "森林", "滨水", "雪景", "荒漠"], "v3")
            ac4, ac5, ac6 = st.columns(3)
            with ac4: viz_render = custom_select("渲染", ["V-Ray", "UE5", "Lumion", "Corona"], "v4")
            with ac5: viz_mat = custom_select("材质", ["混凝土", "玻璃", "木格栅", "涂料", "红砖"], "v5")
            with ac6: viz_mood = custom_select("氛围", ["史诗", "宁静", "科幻", "极简"], "v6")
        elif "建筑设计" in mode:
            st.caption("📐 **设计概念参数**")
            d1, d2, d3 = st.columns(3)
            with d1: des_type = custom_select("图纸", ["草图", "轴测图", "平面图", "剖面图", "素模"], "d1")
            with d2: des_style = custom_select("流派", ["扎哈", "柯布西耶", "安藤", "BIG", "解构"], "d2")
            with d3: des_scale = custom_select("尺度", ["摩天楼", "博物馆", "独栋", "规划"], "d3")
            d4, d5, d6 = st.columns(3)
            with d4: des_mat = custom_select("模型", ["卡纸", "椴木", "亚克力", "铁丝"], "d4")
            with d5: des_bg = custom_select("背景", ["纯白", "网格纸", "牛皮纸"], "d5")
            with d6: des_detail = custom_select("细节", ["高度详细", "概念抽象", "结构构造"], "d6")
        else:
            col_a, col_b, col_c = st.columns(3)
            with col_a: lighting = custom_select("光线", ["自然光", "电影光", "霓虹"], "g1")
            with col_b: camera = custom_select("视角", ["广角", "微距", "鸟瞰"], "g2")
            with col_c: mood = custom_select("氛围", ["梦幻", "史诗", "阴郁"], "g3")
        
        st.markdown("---")
        mp1, mp2 = st.columns(2)
        with mp1: stylize = st.slider("风格化 (--s)", 0, 1000, 250)
        with mp2: chaos = st.slider("多样性 (--c)", 0, 100, 0)
        negative_prompt = st.text_input("🚫 负面词 (--no)", value="text, watermark, blurry, low quality")

    if st.button("🚀 立即生成", type="primary"):
        try:
            client = OpenAI(api_key=st.secrets["API_KEY"], base_url=base_url)
            details = []
            if "效果图" in mode:
                if viz_view != "不指定": details.append(f"View: {viz_view}")
                if viz_time != "不指定": details.append(f"Time: {viz_time}")
                if viz_env != "不指定": details.append(f"Env: {viz_env}")
                if viz_render != "不指定": details.append(f"Render: {viz_render}")
                if viz_mat != "不指定": details.append(f"Mat: {viz_mat}")
                if viz_mood != "不指定": details.append(f"Mood: {viz_mood}")
            elif "建筑设计" in mode:
                if des_type != "不指定": details.append(f"Type: {des_type}")
                if des_style != "不指定": details.append(f"Style: {des_style}")
                if des_scale != "不指定": details.append(f"Scale: {des_scale}")
                if des_mat != "不指定": details.append(f"Mat: {des_mat}")
                if des_bg != "不指定": details.append(f"BG: {des_bg}")
                if des_detail != "不指定": details.append(f"Detail: {des_detail}")
            else:
                if lighting != "不指定": details.append(f"Light: {lighting}")
                if camera != "不指定": details.append(f"Cam: {camera}")
                if mood != "不指定": details.append(f"Mood: {mood}")

            sys_msg = """
            Generate Plan A (Faithful) and Plan B (Creative). 
            Format:
            ===PLAN_A_CN===
            [Chinese A]
            ===PLAN_A_EN===
            [English A]
            ===PLAN_B_CN===
            [Chinese B]
            ===PLAN_B_EN===
            [English B]
            """
            full_req = f"User Input: {user_input}. Req: {', '.join(details)}. Mode: {mode}"
            
            with st.spinner('AI 构思中...'):
                resp = client.chat.completions.create(model=text_model, messages=[{"role":"system","content":sys_msg}, {"role":"user","content":full_req}])
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
        except Exception as e: st.error(f"API Error: {e}")

    if st.session_state.last_results:
        res = st.session_state.last_results
        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### 🅰️ 方案 A"); st.info(res['p1_cn']); st.code(res['p1_en'])
            if st.button("❤️ 收藏 A", key="btn_a"): save_data_item({"category": "默认", "desc": res["p1_cn"][:20], "prompt": res["p1_en"]}, st.session_state.current_user)
        with col_b:
            st.markdown("#### 🅱️ 方案 B"); st.info(res['p2_cn']); st.code(res['p2_en'])
            if st.button("❤️ 收藏 B", key="btn_b"): save_data_item({"category": "默认", "desc": res["p2_cn"][:20], "prompt": res["p2_en"]}, st.session_state.current_user)

# --- Tab 2 ---
with tab2:
    up_file = st.file_uploader("上传图片", type=["jpg", "png"])
    if up_file and st.button("🔍 反推"):
        try:
            client = OpenAI(api_key=st.secrets["API_KEY"], base_url=base_url)
            b64 = encode_image(up_file)
            with st.spinner('Thinking...'):
                resp = client.chat.completions.create(model=vision_model, messages=[{"role":"user","content":[{"type":"text","text":"输出格式：\nCN: [中文]\nEN: [MJ Prompt]"},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}] )
            raw = resp.choices[0].message.content
            if "EN:" in raw:
                cn, en = raw.split("EN:")[0].replace("CN:", "").strip(), raw.split("EN:")[1].strip()
                st.image(up_file, width=200); st.info(cn); st.code(en)
                if st.button("❤️ 收藏"): save_data_item({"category": "反推", "desc": cn[:20], "prompt": en}, st.session_state.current_user)
        except Exception as e: st.error(str(e))

# --- Tab 3 ---
with tab3:
    curr_user = st.session_state.current_user
    st.markdown(f"#### 🌟 {curr_user} 的云端宝库")
    data = load_data(curr_user)
    
    col_h, col_b = st.columns([3, 1])
    with col_b:
        if data and HAS_DOCX:
            docx = generate_word(data)
            st.download_button("📥 导出 Word", data=docx, file_name=f"{curr_user}_prompts.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    
    st.divider()
    with st.expander("➕ 手动添加"):
        with st.form("add_new"):
            cats = sorted(list(set([d['category'] for d in data]))) if data else ["建筑", "人像"]
            c_mode = st.selectbox("分类", ["📝 新建..."] + cats)
            new_c = st.text_input("新分类名") if c_mode == "📝 新建..." else c_mode
            desc = st.text_input("备注")
            cont = st.text_area("内容")
            if st.form_submit_button("保存"):
                save_data_item({"category": new_c, "desc": desc, "prompt": cont}, curr_user)
                st.rerun()
    
    if not data: st.info("宝库是空的")
    else:
        f_cat = st.selectbox("筛选", ["全部"] + sorted(list(set([d['category'] for d in data]))))
        for i in range(len(data)-1, -1, -1):
            d = data[i]
            if f_cat == "全部" or d['category'] == f_cat:
                with st.container(border=True):
                    c1, c2 = st.columns([6,1])
                    with c1: st.markdown(f"**🏷️ [{d['category']}]** {d.get('desc','')} \n\n `{d['prompt']}`")
                    with c2: 
                        if st.button("🗑️", key=f"del_{i}"): delete_data_item(i, curr_user)
