import streamlit as st
from openai import OpenAI
import base64
import json
import requests
import time
import io
from docx import Document

# 1. 页面基本设置
st.set_page_config(page_title="AI 提示词魔法师 Pro", page_icon="🪄", layout="centered")
st.title("✨ AI 提示词魔法师 Pro")

# ================= 🛠️ 工具函数区 =================

def get_gitee_config():
    """获取 Gitee 配置"""
    return {
        "token": st.secrets.get("GITEE_TOKEN", ""),
        "owner": st.secrets.get("GITEE_OWNER", ""),
        "repo": st.secrets.get("GITEE_REPO", ""),
        "path": st.secrets.get("GITEE_PATH", "")
    }

def load_data():
    """从 Gitee 读取数据"""
    try:
        cfg = get_gitee_config()
        if not cfg["token"]: return [] # 没配 Token 就返回空
        
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"
        res = requests.get(url, params={"access_token": cfg['token']})
        
        if res.status_code == 200:
            content = res.json()['content']
            decoded = base64.b64decode(content).decode('utf-8')
            return json.loads(decoded)
        return []
    except:
        return []

def save_data_item(new_item):
    """保存数据到 Gitee"""
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"
        
        # 1. 获取旧文件 (为了拿到 sha)
        get_res = requests.get(url, params={"access_token": cfg['token']})
        if get_res.status_code != 200:
            st.error("连接 Gitee 失败，请检查 Secrets 配置")
            return

        file_info = get_res.json()
        sha = file_info['sha']
        
        # 2. 解析旧数据
        try:
            old_text = base64.b64decode(file_info['content']).decode('utf-8')
            data_list = json.loads(old_text)
        except:
            data_list = []
            
        # 3. 追加新数据
        data_list.append(new_item)
        
        # 4. 重新编码并上传
        new_text = json.dumps(data_list, ensure_ascii=False, indent=4)
        new_b64 = base64.b64encode(new_text.encode('utf-8')).decode('utf-8')
        
        payload = {
            "access_token": cfg['token'],
            "content": new_b64,
            "sha": sha,
            "message": "Add item from Streamlit"
        }
        
        put_res = requests.put(url, json=payload)
        if put_res.status_code == 200:
            st.toast("✅ 已同步到云端！")
            time.sleep(1) # 等一秒防止刷新太快
        else:
            st.error(f"同步失败: {put_res.text}")
            
    except Exception as e:
        st.error(f"保存出错: {e}")

def delete_data_item(index):
    """删除数据"""
    try:
        cfg = get_gitee_config()
        url = f"https://gitee.com/api/v5/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['path']}"
        
        get_res = requests.get(url, params={"access_token": cfg['token']})
        file_info = get_res.json()
        sha = file_info['sha']
        
        data_list = json.loads(base64.b64decode(file_info['content']).decode('utf-8'))
        
        if 0 <= index < len(data_list):
            data_list.pop(index)
            
        new_b64 = base64.b64encode(json.dumps(data_list, ensure_ascii=False, indent=4).encode('utf-8')).decode('utf-8')
        
        payload = {"access_token": cfg['token'], "content": new_b64, "sha": sha, "message": "Delete item"}
        requests.put(url, json=payload)
        st.toast("🗑️ 删除成功")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"删除失败: {e}")

def generate_word(data):
    """生成 Word 文档"""
    doc = Document()
    doc.add_heading('🌟 我的 AI 提示词宝库', 0)
    
    # 获取所有分类并排序
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

# ================= 🔐 侧边栏设置 =================

if "cached_api_key" not in st.session_state:
    st.session_state.cached_api_key = None
if "last_results" not in st.session_state:
    st.session_state.last_results = None

with st.sidebar:
    st.header("🔐 身份验证")
    sys_pass = st.secrets.get("APP_PASSWORD", "")
    sys_key = st.secrets.get("API_KEY", "")
    
    user_pass = st.text_input("🔑 访问密码", type="password")
    
    if user_pass and user_pass == sys_pass:
        st.session_state.cached_api_key = sys_key
        st.success("✅ 已登录")
    elif user_pass:
        st.error("❌ 密码错误")

    st.markdown("---")
    st.header("⚙️ 模型设置")
    base_url = st.text_input("API 地址", value="https://hk-api.gptbest.vip/v1")
    text_model = st.text_input("文本模型", value="deepseek-chat")
    vision_model = st.text_input("视觉模型", value="gpt-4o-mini")

# ================= 🏗️ 主界面 Tabs =================

tab1, tab2, tab3 = st.tabs(["📝 文本生成", "🖼️ 图片反推", "🌟 云端宝库"])

# --- Tab 1: 文本生成 ---
with tab1:
    st.subheader("✍️ 描述画面，生成双方案")
    user_input = st.text_area("你想画什么？", height=100, placeholder="例如：赛博朋克风格的街道...")
    
    c1, c2 = st.columns(2)
    with c1: ratio = st.selectbox("画幅", ["--ar 16:9", "--ar 3:4", "--ar 1:1", "--ar 9:16"])
    with c2: mode = st.selectbox("模式", ["🏗️ 建筑效果图", "标准模式", "自然语言", "二次元"])

    # 高级参数折叠区
    with st.expander("🎨 高级参数"):
        if "建筑" in mode:
            ac1, ac2 = st.columns(2)
            with ac1: arch_view = st.selectbox("视角", ["不指定", "人视", "鸟瞰", "透视"])
            with ac2: arch_time = st.selectbox("时刻", ["不指定", "蓝调", "黄金时刻", "日景"])
        else:
            col_a, col_b = st.columns(2)
            with col_a: lighting = st.selectbox("光线", ["不指定", "自然光", "电影光", "霓虹"])
            with col_b: mood = st.selectbox("氛围", ["不指定", "梦幻", "史诗", "阴郁"])

    if st.button("🚀 开始生成", type="primary"):
        if not st.session_state.cached_api_key:
            st.error("请先在左侧输入密码！")
            st.stop()
            
        try:
            client = OpenAI(api_key=st.session_state.cached_api_key, base_url=base_url)
            
            # 简化的 Prompt 指令
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
            req_msg = f"Request: {user_input}. Mode: {mode}. Ratio: {ratio}"
            
            with st.spinner('AI 正在构思...'):
                resp = client.chat.completions.create(
                    model=text_model,
                    messages=[{"role":"system","content":sys_msg}, {"role":"user","content":req_msg}]
                )
                
                raw = resp.choices[0].message.content
                
                # 结果解析逻辑
                try:
                    p1_cn = raw.split("===PLAN_A_EN===")[0].replace("===PLAN_A_CN===", "").strip()
                    p1_en = raw.split("===PLAN_B_CN===")[0].split("===PLAN_A_EN===")[1].strip() + f" {ratio}"
                    p2_cn = raw.split("===PLAN_B_EN===")[0].split("===PLAN_B_CN===")[1].strip()
                    p2_en = raw.split("===PLAN_B_EN===")[1].strip() + f" {ratio}"
                except:
                    p1_cn, p1_en, p2_cn, p2_en = "解析失败", raw, "解析失败", raw
                
                # 存入缓存
                st.session_state.last_results = {
                    "p1_cn": p1_cn, "p1_en": p1_en,
                    "p2_cn": p2_cn, "p2_en": p2_en
                }
                
        except Exception as e:
            st.error(f"请求出错: {e}")

    # 显示结果
    if st.session_state.last_results:
        res = st.session_state.last_results
        st.divider()
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.info(f"方案 A: {res['p1_cn']}")
            st.code(res['p1_en'])
            if st.button("❤️ 收藏 A"):
                save_data_item({"category": "默认", "desc": res["p1_cn"][:20], "prompt": res["p1_en"]})
                
        with col_b:
            st.info(f"方案 B: {res['p2_cn']}")
            st.code(res['p2_en'])
            if st.button("❤️ 收藏 B"):
                save_data_item({"category": "默认", "desc": res["p2_cn"][:20], "prompt": res["p2_en"]})

# --- Tab 2: 图片反推 ---
with tab2:
    st.subheader("🖼️ 图片反推")
    up_file = st.file_uploader("上传图片", type=["jpg", "png"])
    
    if up_file and st.button("🔍 开始反推"):
        if not st.session_state.cached_api_key:
            st.error("请先输入密码")
            st.stop()
            
        try:
            client = OpenAI(api_key=st.session_state.cached_api_key, base_url=base_url)
            b64_img = encode_image(up_file)
            
            with st.spinner('正在观察图片...'):
                resp = client.chat.completions.create(
                    model=vision_model,
                    messages=[{
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": "输出格式：\nCN: [中文描述]\nEN: [MJ Prompt]"}, 
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                        ]
                    }] 
                )
                
            raw = resp.choices[0].message.content
            if "EN:" in raw:
                cn = raw.split("EN:")[0].replace("CN:", "").strip()
                en = raw.split("EN:")[1].strip()
                
                st.image(up_file, width=200)
                st.info(cn)
                st.code(en)
                
                if st.button("❤️ 收藏结果"):
                    save_data_item({"category": "反推", "desc": cn[:20], "prompt": en})
                    
        except Exception as e:
            st.error(f"反推失败: {e}")

# --- Tab 3: 云端宝库 ---
with tab3:
    st.header("🌟 云端提示词宝库")
    
    # 加载数据
    data = load_data()
    
    if data:
        # Word 导出按钮
        word_file = generate_word(data)
        st.download_button(
            label="📥 导出 Word 文档",
            data=word_file,
            file_name="我的提示词库.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    
    st.divider()
    
    # 手动添加区
    with st.expander("➕ 手动添加新提示词"):
        with st.form("add_form"):
            # 获取现有分类
            cats = sorted(list(set([d['category'] for d in data]))) if data else ["建筑", "人像"]
            
            cat_mode = st.selectbox("选择分类", ["📝 新建分类..."] + cats)
            custom_cat = ""
            if cat_mode == "📝 新建分类...":
                custom_cat = st.text_input("输入新分类名称")
            
            desc = st.text_input("备注名称")
            content = st.text_area("提示词内容")
            
            if st.form_submit_button("💾 保存"):
                final_cat = custom_cat if cat_mode == "📝 新建分类..." else cat_mode
                if final_cat and content:
                    save_data_item({"category": final_cat, "desc": desc, "prompt": content})
                    st.rerun()
                else:
                    st.warning("分类和内容不能为空")

    st.divider()
    
    # 列表展示
    if not data:
        st.info("📭 暂无数据，快去添加吧！")
    else:
        # 筛选
        all_cats = ["全部"] + sorted(list(set([d['category'] for d in data])))
        sel_cat = st.selectbox("📂 筛选分类", all_cats)
        
        # 倒序遍历
        for i in range(len(data)-1, -1, -1):
            d = data[i]
            if sel_cat == "全部" or d['category'] == sel_cat:
                with st.container(border=True):
                    c1, c2 = st.columns([6, 1])
                    with c1:
                        st.markdown(f"**🏷️ [{d['category']}] {d.get('desc', '无标题')}**")
                        st.code(d['prompt'])
                    with c2:
                        if st.button("🗑️", key=f"del_{i}"):
                            delete_data_item(i)
