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
import re
from datetime import datetime

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
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #ff9a44 0%, #fc6076 100%); border: none; color: white !important;
            padding: 12px 28px; border-radius: 8px; font-weight: 600; font-size: 16px; width: 100%; transition: all 0.3s;
            box-shadow: 0 4px 12px rgba(252, 96, 118, 0.3);
        }
        div.stButton > button[kind="primary"]:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(252, 96, 118, 0.4); }
        .stCode { background-color: #f8f9fa !important; border: 1px solid #eee; border-radius: 8px; }
        .stInfo { background-color: #f0f7ff; color: #0052cc; border: none; border-radius: 8px; }
        .stSuccess { background-color: #e6fffa; color: #009975; border: none; border-radius: 8px; }
        /* 复制按钮点击后反馈 */
        button[kind="secondary"] { min-height: 36px; }
    </style>
    <script>
        function resetCopyBtn(btn) {
            setTimeout(() => { btn.innerText = '📋 复制中文'; }, 1500);
        }
    </script>
    """, unsafe_allow_html=True)

add_modern_light_style()

# ================= 🛠️ Gitee 核心函数 =================
def get_gitee_config():
    return {
        "token": st.secrets.get("GITEE_TOKEN", ""),
        "owner": st.secrets.get("GITEE_OWNER", ""),
        "repo": st.secrets.get("GITEE_REPO", "")
    }

def get_default_branch():
    """自动检测仓库默认分支（main 或 master）"""
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}"
        res = requests.get(url, params={"access_token": cfg['token']})
        if res.status_code == 200:
            return res.json().get("default_branch", "main")
    except:
        pass
    return "main"  # 失败时默认 main

BRANCH = get_default_branch()  # 全局分支

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_username(username):
    return bool(re.match(r"^[a-zA-Z0-9_-]{3,20}$", username))

def get_all_users():
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/users.json"
        res = requests.get(url, params={"access_token": cfg['token'], "ref": BRANCH})
        if res.status_code == 200:
            content = res.json()['content']
            decoded = base64.b64decode(content).decode('utf-8')
            data = json.loads(decoded)
            if isinstance(data, list):
                return {}
            return data
        return {}
    except:
        return {}

def register_new_user(username, password):
    if not validate_username(username):
        return False, "❌ 用户名只能包含字母数字下划线和连字符，长度3-20"
   
    users = get_all_users()
    if username in users:
        return False, "❌ 用户名已存在"
   
    users[username] = hash_password(password)
   
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/users.json"
        sha = None
        get_res = requests.get(url, params={"access_token": cfg['token'], "ref": BRANCH})
        if get_res.status_code == 200:
            sha = get_res.json()['sha']
       
        new_text = json.dumps(users, ensure_ascii=False, indent=4)
        new_b64 = base64.b64encode(new_text.encode('utf-8')).decode('utf-8')
       
        payload = {
            "access_token": cfg['token'],
            "content": new_b64,
            "message": f"Register user {username}",
            "branch": BRANCH
        }
        if sha: payload["sha"] = sha
       
        res = requests.put(url, json=payload)
        if res.status_code in [200, 201]:
            return True, "✅ 注册成功！已自动登录"
        else:
            return False, f"注册失败: {res.text}"
    except Exception as e:
        return False, str(e)

# --- 数据存储系统（同理使用 BRANCH） ---
def get_user_filename(username):
    return f"prompts_{username}.json"

def load_data(username):
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{get_user_filename(username)}"
        res = requests.get(url, params={"access_token": cfg['token'], "ref": BRANCH})
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
        return []
    except:
        return []

def save_data_item(new_item, username):
    new_item["timestamp"] = datetime.now().isoformat()
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{get_user_filename(username)}"
        res = requests.get(url, params={"access_token": cfg['token'], "ref": BRANCH})
        sha, data_list = None, []
        if res.status_code == 200:
            sha = res.json()['sha']
            try: data_list = json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
            except: data_list = []
        else:
            data_list = []
        data_list.append(new_item)
        new_b64 = base64.b64encode(json.dumps(data_list, ensure_ascii=False, indent=4).encode('utf-8')).decode('utf-8')
        payload = {
            "access_token": cfg['token'],
            "content": new_b64,
            "message": f"Add prompt by {username}",
            "branch": BRANCH
        }
        if sha: payload["sha"] = sha
        requests.put(url, json=payload)
        st.toast(f"✅ 已保存到 {username} 的宝库")
        time.sleep(1)
    except Exception as e:
        st.error(f"保存出错: {e}")

def delete_data_item(index, username):
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{get_user_filename(username)}"
        res = requests.get(url, params={"access_token": cfg['token'], "ref": BRANCH})
        if res.status_code == 200:
            info = res.json()
            data = json.loads(base64.b64decode(info['content']).decode('utf-8'))
            if 0 <= index < len(data):
                data.pop(index)
                new_b64 = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8')).decode('utf-8')
                requests.put(url, json={
                    "access_token": cfg['token'],
                    "content": new_b64,
                    "sha": info['sha'],
                    "message": f"Delete by {username}",
                    "branch": BRANCH
                })
                st.toast("🗑️ 删除成功")
                time.sleep(1)
                st.rerun()
    except:
        pass

# 其余函数（generate_word, encode_image, custom_select, generate_qr_code）保持不变
def generate_word(data):
    if not HAS_DOCX: return None
    doc = Document()
    doc.add_heading('🌟 我的 AI 提示词宝库', 0)
    doc.add_paragraph(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    doc.add_paragraph(f"用户名: {st.session_state.current_user}\n")
    cats = sorted(list(set([d['category'] for d in data])))
    for cat in cats:
        doc.add_heading(f"📂 {cat}", level=1)
        items = sorted([d for d in data if d['category'] == cat],
                       key=lambda x: x.get('timestamp', ''), reverse=True)
        for item in items:
            doc.add_heading(item.get('desc', '无标题'), level=2)
            doc.add_paragraph(f"时间: {item.get('timestamp', '未知')}")
            doc.add_paragraph(item['prompt'])
            doc.add_paragraph("-" * 50)
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def encode_image(file):
    return base64.b64encode(file.getvalue()).decode('utf-8')

def custom_select(label, options, key_suffix):
    selected = st.selectbox(label, ["不指定"] + options + ["📝 自定义输入..."], key=f"sel_{key_suffix}")
    if selected == "📝 自定义输入...":
        val = st.text_input(f"请输入 {label}", key=f"txt_{key_suffix}")
        return val if val.strip() else "不指定"
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
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "last_results" not in st.session_state:
    st.session_state.last_results = None

# URL 自动登录
if not st.session_state.current_user:
    params = st.query_params.to_dict()
    u_arg = params.get("u")
    p_arg = params.get("p")
    if u_arg and p_arg:
        users_db = get_all_users()
        try:
            decoded_p = base64.b64decode(p_arg).decode('utf-8')
            hashed_p = hash_password(decoded_p)
            if u_arg in users_db and users_db[u_arg] == hashed_p:
                st.session_state.current_user = u_arg
                st.toast(f"🎉 扫码登录成功！欢迎 {u_arg}")
                time.sleep(1)
                st.rerun()
        except:
            pass

# ================= 🔐 侧边栏 =================
with st.sidebar:
    st.markdown("### 🔐 账户中心")
   
    if st.session_state.current_user:
        st.success(f"👤 已登录: **{st.session_state.current_user}**")
       
        with st.expander("📱 生成免密二维码"):
            st.caption("朋友扫此码可直接登录你的账号")
            confirm_pass = st.text_input("验证当前密码以生成", type="password", key="qr_pass_sid")
            if confirm_pass:
                users_db = get_all_users()
                if users_db.get(st.session_state.current_user) == hash_password(confirm_pass):
                    b64_pass = base64.b64encode(confirm_pass.encode()).decode()
                    # 动态获取当前页面完整 URL（兼容所有部署）
                    current_url = st.runtime.scriptrunner.get_url()
                    if not current_url:
                        current_url = "https://your-app-name.streamlit.app"  # 备用
                    login_link = f"{current_url}?u={st.session_state.current_user}&p={b64_pass}"
                    qr_img = generate_qr_code(login_link)
                    st.image(qr_img, caption="微信扫一扫，免密直连")
                    st.code(login_link, language=None)
                else:
                    st.error("密码错误")
       
        if st.button("退出登录"):
            st.session_state.current_user = None
            st.rerun()
    else:
        auth_mode = st.radio("选择模式", ["登录", "注册新账号"], horizontal=True)
        user_input_name = st.text_input("用户名", placeholder="英文/数字/下划线", key="login_name")
        user_input_pass = st.text_input("密码", type="password", key="login_pass")
       
        if auth_mode == "登录":
            if st.button("登录", type="primary"):
                if not validate_username(user_input_name):
                    st.error("用户名格式无效")
                else:
                    users_db = get_all_users()
                    hashed_pw = hash_password(user_input_pass)
                    if user_input_name in users_db and users_db[user_input_name] == hashed_pw:
                        st.session_state.current_user = user_input_name
                        st.success("✅ 登录成功！")
                        st.rerun()
                    else:
                        st.error("❌ 用户名或密码错误")
        else:
            if st.button("✨ 立即注册"):
                success, msg = register_new_user(user_input_name, user_input_pass)
                if success:
                    st.session_state.current_user = user_input_name
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
   
    st.markdown("---")
    st.markdown("### ⚙️ 系统设置")
    base_url = st.text_input("API 地址", value="https://hk-api.gptbest.vip/v1")
    text_model = st.text_input("文本模型", value="deepseek-chat")
    vision_model = st.text_input("视觉模型", value="gpt-4o-mini")

# ================= 🏗️ 主界面及所有 Tab（保持之前优化，包括复制按钮）=================
# （由于篇幅限制，这里只贴出关键的 Tab1 结果展示部分，其他部分与上个版本完全一致）

st.markdown("# 🍊 AI Prompt Wizard <small>Pro</small>", unsafe_allow_html=True)
if not st.session_state.current_user:
    st.info("👋 欢迎！请在左侧 **登录** 或 **注册** 一个账号开始使用。")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📝 生成提示词", "🖼️ 图片反推", "🌟 我的云端宝库"])

with tab1:
    # （输入区代码保持不变，略）
    # ... [你的输入和生成逻辑，与之前完全相同]

    if st.session_state.last_results:
        res = st.session_state.last_results
        st.divider()
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("#### 🅰️ 方案 A（忠实版）")
            st.markdown(f"""
            <div style="position: relative;">
                <div style="background-color: #f0f7ff; border-left: 4px solid #0052cc; padding: 14px 18px; border-radius: 8px; margin-bottom: 16px; line-height: 1.6; white-space: pre-wrap;">
                    {res['p1_cn']}
                </div>
                <button onclick="navigator.clipboard.writeText(`{res['p1_cn'].replace('`', '\\`')}`); this.innerText='✓ 已复制'; resetCopyBtn(this)" 
                        style="position: absolute; top: 10px; right: 10px; background: rgba(0,82,204,0.12); border: none; border-radius: 6px; padding: 8px 12px; cursor: pointer; font-size: 13px; color: #0052cc; font-weight: 600;">
                    📋 复制中文
                </button>
            </div>
            """, unsafe_allow_html=True)
            st.code(res['p1_en'], language="text", height=220)
            if st.button("❤️ 收藏方案 A", key="save_a"):
                save_data_item({"category": "生成记录", "desc": res["p1_cn"][:30]+"..." if len(res["p1_cn"])>30 else res["p1_cn"], "prompt": res["p1_en"]}, st.session_state.current_user)

        with col_b:
            st.markdown("#### 🅱️ 方案 B（创意版）")
            st.markdown(f"""
            <div style="position: relative;">
                <div style="background-color: #f0f7ff; border-left: 4px solid #0052cc; padding: 14px 18px; border-radius: 8px; margin-bottom: 16px; line-height: 1.6; white-space: pre-wrap;">
                    {res['p2_cn']}
                </div>
                <button onclick="navigator.clipboard.writeText(`{res['p2_cn'].replace('`', '\\`')}`); this.innerText='✓ 已复制'; resetCopyBtn(this)" 
                        style="position: absolute; top: 10px; right: 10px; background: rgba(0,82,204,0.12); border: none; border-radius: 6px; padding: 8px 12px; cursor: pointer; font-size: 13px; color: #0052cc; font-weight: 600;">
                    📋 复制中文
                </button>
            </div>
            """, unsafe_allow_html=True)
            st.code(res['p2_en'], language="text", height=220)
            if st.button("❤️ 收藏方案 B", key="save_b"):
                save_data_item({"category": "生成记录", "desc": res["p2_cn"][:30]+"..." if len(res["p2_cn"])>30 else res["p2_cn"], "prompt": res["p2_en"]}, st.session_state.current_user)

# Tab2、Tab3 与上个版本完全一致（包括图片反推的复制按钮），这里不再重复。

st.caption("🍊 AI Prompt Wizard Pro | 基于 Gitee 云存储 | 2025.12 最终优化版")
