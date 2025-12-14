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
st.set_page_config(page_title="AI 提示词魔法师 Pro", page_icon="🍊", layout="centered")

# ================= 🎨 UI：现代极简亮白风格 =================
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
    </style>
    """, unsafe_allow_html=True)

add_modern_light_style()

# ================= 🛠️ 后端工具函数 =================

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
        if res.status_code != 200: st.error("Gitee 连接失败"); return
        
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
            p = doc.add_paragraph(item['prompt'])
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
    st.markdown("### ⚙️ 模型设置")
    base_url = st.text_input("API 地址", value="https://hk-api.gptbest.vip/v1")
    text_model = st.text_input("文本模型", value="deepseek-chat")
    vision_model = st.text_input("视觉模型", value="gpt-4o-mini")

# ================= 🏗️ 主界面 =================
st.markdown("# 🍊 AI Prompt Wizard <small>Pro</small>", unsafe_allow_html=True)
st.caption("建筑/摄影/设计提示词生成器 | Powered by DeepSeek")

tab1, tab2, tab3 = st.tabs(["📝 生成提示词", "🖼️ 图片反推", "🌟 云端宝库"])

# --- Tab 1: 文本生成 (专业升级版) ---
with tab1:
    st.markdown("##### ✍️ 描述画面")
    user_input = st.text_area("输入", height=100, label_visibility="collapsed", placeholder="例如：一个极简风格的白色美术馆，光影交错...")
    
    c1, c2 = st.columns(2)
    with c1: 
        ratio = st.selectbox("画幅比例", ["--ar 16:9", "--ar 3:4", "--ar 1:1", "--ar 9:16", "--ar 2:3"])
    with c2: 
        # 👇 选项拆分：效果图 vs 建筑设计
        mode = st.selectbox("生成模式", [
            "🏢 建筑效果图 (ArchViz)", 
            "📐 建筑设计 (Design Concept)", 
            "标准模式 (MJ/SD)", 
            "自然语言 (Google)", 
            "二次元 (Niji)", 
            "写实摄影"
        ])

    # ✨✨✨ 动态高级选项 (建筑双模式优化) ✨✨✨
    with st.expander("🎨 高级参数配置 (点击展开详细设置)", expanded=True):
        
        # 🔴 模式 1：建筑效果图 (侧重渲染、环境、氛围)
        if "效果图" in mode:
            st.caption("🏢 **ArchViz 效果图专用参数**")
            ac1, ac2, ac3 = st.columns(3)
            with ac1: viz_view = st.selectbox("📐 构图视点", ["不指定", "人视 (Eye Level)", "半鸟瞰 (Semi-Aerial)", "顶视图 (Top View)", "虫视 (Worm's Eye)", "一点透视"])
            with ac2: viz_time = st.selectbox("🌤️ 天气时刻", ["不指定", "黄金时刻 (Golden Hour)", "蓝调时刻 (Blue Hour)", "正午 (Noon)", "阴天 (Overcast)", "雨夜 (Rainy)"])
            with ac3: viz_env = st.selectbox("🌳 周边环境", ["不指定", "繁华街道", "森林景观", "滨水/海边", "雪景", "荒漠", "极简棚拍"])
            
            ac4, ac5, ac6 = st.columns(3)
            with ac4: viz_render = st.selectbox("🖥️ 渲染引擎", ["不指定", "V-Ray 逼真", "Unreal Engine 5", "Lumion 风格", "Corona Render", "D5 渲染器"])
            with ac5: viz_mat = st.selectbox("🧶 表面材质", ["不指定", "清水混凝土", "高反光玻璃", "木格栅", "白色涂料", "红砖", "耐候钢"])
            with ac6: viz_mood = st.selectbox("🎭 渲染氛围", ["不指定", "史诗感 (Epic)", "宁静致远 (Serene)", "科幻未来 (Sci-Fi)", "极简主义 (Minimalist)"])

        # 🟠 模式 2：建筑设计 (侧重流派、图纸、概念)
        elif "建筑设计" in mode:
            st.caption("📐 **Architectural Design 设计概念专用参数**")
            d1, d2, d3 = st.columns(3)
            with d1: des_type = st.selectbox("✏️ 图纸类型", ["不指定", "概念草图 (Sketch)", "轴测分析图 (Axonometric)", "平面图 (Plan)", "剖面图 (Section)", "素模渲染 (Clay Model)", "蓝图 (Blueprint)"])
            with d2: des_style = st.selectbox("🏛️ 设计流派", ["不指定", "扎哈·哈迪德 (曲线)", "柯布西耶 (现代)", "安藤忠雄 (清水)", "BIG (图解)", "解构主义", "高技派", "新中式"])
            with d3: des_scale = st.selectbox("📏 建筑尺度", ["不指定", "摩天大楼", "大型公建/博物馆", "独栋住宅/别墅", "城市规划 (Masterplan)", "装置艺术 (Pavilion)"])
            
            d4, d5, d6 = st.columns(3)
            with d4: des_mat = st.selectbox("🧱 概念材质", ["不指定", "白色卡纸模型", "椴木模型", "透明亚克力", "铁丝网架", "乐高风格"])
            with d5: des_bg = st.selectbox("⬜ 背景风格", ["不指定", "纯白背景", "网格纸背景", "牛皮纸背景", "渐变背景"])
            with d6: des_detail = st.selectbox("🔍 细节程度", ["不指定", "高度详细 (Highly Detailed)", "概念抽象 (Abstract)", "结构构造 (Tectonic)"])

        # 🔵 模式 3：通用/其他
        else:
            st.caption("🎨 **通用参数面板**")
            col_a, col_b, col_c = st.columns(3)
            with col_a: lighting = st.selectbox("💡 光线氛围", ["不指定", "自然光", "电影级布光", "黄金时刻", "赛博霓虹", "柔和光"])
            with col_b: camera = st.selectbox("📷 镜头视角", ["不指定", "广角", "微距", "鸟瞰", "人视", "鱼眼"])
            with col_c: mood = st.selectbox("🎭 情绪氛围", ["不指定", "梦幻", "史诗感", "阴郁", "宁静", "活力"])

        st.markdown("---")
        # MJ 参数与负面词
        mp1, mp2 = st.columns(2)
        with mp1: stylize = st.slider("风格化程度 (--s)", 0, 1000, 250, help="数值越高画面越艺术")
        with mp2: chaos = st.slider("多样性 (--c)", 0, 100, 0, help="数值越高四张图差异越大")
        
        negative_prompt = st.text_input("🚫 负面提示词 (--no)", value="text, watermark, blurry, low quality, bad anatomy, ugly, distorted")

    # 生成按钮
    if st.button("🚀 立即生成 / Generate", type="primary"):
        if not st.session_state.cached_api_key:
            st.error("请先在侧边栏输入密码解锁！")
            st.stop()
            
        try:
            client = OpenAI(api_key=st.session_state.cached_api_key, base_url=base_url)
            
            # 👇👇👇 智能参数拼接逻辑 👇👇👇
            details = []
            
            if "效果图" in mode:
                # 拼接效果图参数
                if viz_view != "不指定": details.append(f"View: {viz_view}")
                if viz_time != "不指定": details.append(f"Time: {viz_time}")
                if viz_env != "不指定": details.append(f"Env: {viz_env}")
                if viz_render != "不指定": details.append(f"Render Engine: {viz_render}")
                if viz_mat != "不指定": details.append(f"Material: {viz_mat}")
                if viz_mood != "不指定": details.append(f"Mood: {viz_mood}")
                
            elif "建筑设计" in mode:
                # 拼接设计概念参数
                if des_type != "不指定": details.append(f"Drawing Type: {des_type}")
                if des_style != "不指定": details.append(f"Architectural Style: {des_style}")
                if des_scale != "不指定": details.append(f"Scale/Typology: {des_scale}")
                if des_mat != "不指定": details.append(f"Model Material: {des_mat}")
                if des_bg != "不指定": details.append(f"Background: {des_bg}")
                if des_detail != "不指定": details.append(f"Detail Level: {des_detail}")
                
            else:
                # 拼接通用参数
                if lighting != "不指定": details.append(f"Light: {lighting}")
                if camera != "不指定": details.append(f"Cam: {camera}")
                if mood != "不指定": details.append(f"Mood: {mood}")

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
            
            full_req = f"User Input: {user_input}. Requirements: {', '.join(details)}. Mode: {mode}"
            
            with st.spinner('✨ AI 正在构思方案...'):
                resp = client.chat.completions.create(model=text_model, messages=[{"role":"system","content":sys_msg}, {"role":"user","content":full_req}])
                raw = resp.choices[0].message.content
                
                try:
                    p1_cn = raw.split("===PLAN_A_EN===")[0].replace("===PLAN_A_CN===", "").strip()
                    p1_en = raw.split("===PLAN_B_CN===")[0].split("===PLAN_A_EN===")[1].strip()
                    p2_cn = raw.split("===PLAN_B_EN===")[0].split("===PLAN_B_CN===")[1].strip()
                    p2_en = raw.split("===PLAN_B_EN===")[1].strip()
                except:
                    p1_cn, p1_en, p2_cn, p2_en = "解析失败", raw, "解析失败", raw
                
                # 拼接后缀
                suffix = f" {ratio.split(' ')[0]}"
                if "自然语言" not in mode:
                    suffix += f" --s {stylize} --c {chaos}"
                    if negative_prompt: suffix += f" --no {negative_prompt}"
                
                st.session_state.last_results = {
                    "p1_cn": p1_cn, "p1_en": p1_en + suffix, 
                    "p2_cn": p2_cn, "p2_en": p2_en + suffix
                }
        except Exception as e: st.error(f"API Error: {e}")

    if st.session_state.last_results:
        res = st.session_state.last_results
        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### 🅰️ 方案 A (精准还原)")
            st.info(res['p1_cn'])
            st.code(res['p1_en'])
            if st.button("❤️ 收藏 A", key="btn_a"):
                save_data_item({"category": "默认", "desc": res["p1_cn"][:20], "prompt": res["p1_en"]})
        with col_b:
            st.markdown("#### 🅱️ 方案 B (艺术发散)")
            st.info(res['p2_cn'])
            st.code(res['p2_en'])
            if st.button("❤️ 收藏 B", key="btn_b"):
                save_data_item({"category": "默认", "desc": res["p2_cn"][:20], "prompt": res["p2_en"]})

# --- Tab 2: 图片反推 ---
with tab2:
    st.markdown("##### 🖼️ 上传图片获取提示词")
    up_file = st.file_uploader("Upload Image", type=["jpg", "png"], label_visibility="collapsed")
    if up_file and st.button("🔍 开始反推", type="primary"):
        if not st.session_state.cached_api_key: st.error("请先输入密码"); st.stop()
        try:
            client = OpenAI(api_key=st.session_state.cached_api_key, base_url=base_url)
            b64 = encode_image(up_file)
            with st.spinner('正在分析图片内容...'):
                resp = client.chat.completions.create(model=vision_model, messages=[{"role":"user","content":[{"type":"text","text":"输出格式：\nCN: [中文描述]\nEN: [MJ Prompt]"},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}] )
            raw = resp.choices[0].message.content
            if "EN:" in raw:
                cn, en = raw.split("EN:")[0].replace("CN:", "").strip(), raw.split("EN:")[1].strip()
                st.image(up_file, width=200)
                st.info(cn); st.code(en)
                if st.button("❤️ 收藏结果", key="btn_ocr"): save_data_item({"category": "反推", "desc": cn[:20], "prompt": en})
        except Exception as e: st.error(str(e))

# --- Tab 3: 云端宝库 ---
with tab3:
    data = load_data()
    
    col_head, col_btn = st.columns([3, 1])
    with col_head:
        st.markdown(f"##### 📂 云端知识库 (共 {len(data)} 条)")
    with col_btn:
        if data and HAS_DOCX:
            docx = generate_word(data)
            st.download_button("📥 导出 Word", data=docx, file_name="Prompts.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_doc")
    
    st.divider()
    
    with st.expander("➕ 添加新数据", expanded=False):
        with st.form("add_new"):
            cats = sorted(list(set([d['category'] for d in data]))) if data else ["建筑", "人像"]
            c_mode = st.selectbox("分类", ["📝 新建..."] + cats)
            new_c = st.text_input("输入新分类名") if c_mode == "📝 新建..." else c_mode
            desc = st.text_input("备注")
            cont = st.text_area("内容", placeholder="粘贴提示词...")
            if st.form_submit_button("保存"):
                save_data_item({"category": new_c, "desc": desc, "prompt": cont})
                st.rerun()
    
    if not data: st.info("云端数据库为空，快去添加吧！")
    else:
        f_cat = st.selectbox("筛选分类", ["全部"] + sorted(list(set([d['category'] for d in data]))))
        for i in range(len(data)-1, -1, -1):
            d = data[i]
            if f_cat == "全部" or d['category'] == f_cat:
                with st.container(border=True):
                    c1, c2 = st.columns([6,1])
                    with c1: st.markdown(f"**🏷️ [{d['category']}]** {d.get('desc','')} \n\n `{d['prompt']}`")
                    with c2: 
                        if st.button("🗑️", key=f"del_{i}"): delete_data_item(i)
