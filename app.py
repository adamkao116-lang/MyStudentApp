import streamlit as st
import pandas as pd
from datetime import datetime
import os
from PIL import Image

# ==========================================
# 1. 系統路徑與基礎設定
# ==========================================
DATA_FILE = "attendance_records.csv"     # 點名紀錄存檔
STUDENT_LIST_FILE = "master_list.csv"    # 全班名冊存檔
CLASS_NAME_FILE = "class_info.txt"       # 班級名稱存檔
LOGO_FILE = "school_logo.png"            # 校徽圖檔存檔

# 16 種詳細假別
STATUS_OPTIONS = [
    "準時", "遲未到", "遲后到", "無故曠課",
    "事假半日（上午）", "事假半日（下午）", "事假全日",
    "病假半日（上午）", "病假半日（下午）", "病假全日",
    "公假半日（上午）", "公假半日（下午）", "公假全日",
    "喪假半日（上午）", "喪假半日（下午）", "喪假全日"
]

# ==========================================
# 2. 核心資料讀取與修復邏輯
# ==========================================
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
            # 使用 errors='coerce' 確保日期格式錯誤不會導致當機
            df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
            return df.dropna(subset=['日期'])
        except Exception:
            return pd.DataFrame(columns=["日期", "學生姓名", "狀態", "備註"])
    return pd.DataFrame(columns=["日期", "學生姓名", "狀態", "備註"])

def load_master_list():
    if os.path.exists(STUDENT_LIST_FILE):
        try:
            return pd.read_csv(STUDENT_LIST_FILE, encoding='utf-8-sig')['姓名'].tolist()
        except:
            return []
    return []

def load_class_name():
    if os.path.exists(CLASS_NAME_FILE):
        try:
            with open(CLASS_NAME_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            return "我的班級"
    return "我的班級"

# 初始化資料
records_df = load_data()
students = sorted(load_master_list())
class_name = load_class_name()

# ==========================================
# 3. 網頁佈局 (校徽與標題並排)
# ==========================================
st.set_page_config(page_title=f"{class_name} 點名系統", layout="wide", page_icon="🏫")

col_logo, col_title = st.columns([1, 10]) 

with col_logo:
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, width=80) 
    else:
        st.title("🏫")

with col_title:
    st.title(f"{class_name} 出缺勤管理系統")

st.divider()

# ==========================================
# 4. 功能分頁系統
# ==========================================
tab1, tab2, tab3 = st.tabs(["✅ 批次點名", "📊 報表中心", "🛠️ 系統設定"])

# --- 分頁一：批次點名 ---
with tab1:
    st.header("📝 每日全班點名")
    c_date = st.date_input("點名日期", datetime.now(), key="main_date")
    
    if not students:
        st.warning("⚠️ 目前名冊為空，請先至「系統設定」分頁新增學生名單。")
    else:
        st.info("💡 預設皆為『準時』，僅需修改異常狀態。")
        with st.form("batch_attendance_form"):
            attendance_input = {}
            for s in students:
                c1, c2, c3 = st.columns([2, 3, 4])
                c1.write(f"👤 **{s}**")
                st_val = c2.selectbox("狀態", STATUS_OPTIONS, key=f"status_{s}", label_visibility="collapsed")
                nt_val = c3.text_input("備註", key=f"note_{s}", label_visibility="collapsed", placeholder="點此輸入備註")
                attendance_input[s] = {"狀態": st_val, "備註": nt_val}
            
            if st.form_submit_button("💾 儲存今日全班紀錄", type="primary"):
                new_entries = []
                for name, info in attendance_input.items():
                    new_entries.append({
                        "日期": c_date,
                        "學生姓名": name,
                        "狀態": info["狀態"],
                        "備註": info["備註"]
                    })
                new_df = pd.concat([records_df, pd.DataFrame(new_entries)], ignore_index=True)
                new_df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                st.success(f"✅ {c_date} 資料已儲存！")
                st.rerun()

# --- 分頁二：報表中心 ---
with tab2:
    st.header("🔍 資料查詢與導出")
    rtype = st.radio("模式", ["全班月度統計表", "全班單日檢視", "個人區間追蹤"], horizontal=True)
    
    if rtype == "全班月度統計表":
        cm1, cm2 = st.columns(2)
        s_year = cm1.selectbox("年份", [2025, 2026, 2027], index=1)
        # 注意此行：確保括號完整
        s_month = cm2.selectbox("月份", list(range(1, 13)), index=datetime.now().month-1)
        
        m_data = records_df[(records_df['日期'].dt.year == s_year) & (records_df['日期'].dt.month == s_month)]
        if not m_data.empty:
            grid = m_data.pivot_table(index='學生姓名', columns=m_data['日期'].dt.day, values='狀態', aggfunc='first').fillna("-")
            st.write(f"📅 {s_year} 年 {s_month} 月 報表")
            st.dataframe(grid, use_container_width=True)
            st.download_button("💾 下載全班月報表", grid.to_csv().encode('utf-8-sig'), f"Monthly_{s_year}_{s_month}.csv")
        else:
            st.info("該月份無紀錄。")

    elif rtype == "全班單日檢視":
        target_d = st.date_input("選擇日期", datetime.now())
        day_res = records_df[records_df['日期'].dt.date == target_d]
        if not day_res.empty:
            st.dataframe(day_res, use_container_width=True)
            st.download_button("💾 下載單日報表", day_res.to_csv(index=False).encode('utf-8-sig'), f"Daily_{target_d}.csv")
        else:
            st.info("當天無紀錄。")

    elif rtype == "個人區間追蹤":
        cp1, cp2 = st.columns(2)
        target_s = cp1.selectbox("選擇學生", ["請選擇"] + students)
        p_range = cp2.date_input("區段", [datetime(2026, 1, 1), datetime.now()])
        if target_s != "請選擇" and len(p_range) == 2:
            mask = (records_df['學生姓名'] == target_s) & (records_df['日期'].dt.date >= p_range[0]) & (records_df['日期'].dt.date <= p_range[1])
            p_res = records_df[mask].sort_values("日期", ascending=False)
            st.dataframe(p_res, use_container_width=True)
            st.download_button("💾 下載個人追蹤表", p_res.to_csv(index=False).encode('utf-8-sig'), f"{target_s}_report.csv")

# --- 分頁三：系統設定 ---
with tab3:
    st.header("🛠️ 系統自定義設定")
    with st.expander("🏫 班級形象設定", expanded=True):
        new_name = st.text_input("班級名稱", value=class_name)
        if st.button("更新名稱"):
            with open(CLASS_NAME_FILE, "w", encoding="utf-8") as f:
                f.write(new_name)
            st.success("班級名稱已更新！")
            st.rerun()
        st.divider()
        st.write("上傳新校徽")
        up_logo = st.file_uploader("選擇圖檔", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
        if up_logo:
            img = Image.open(up_logo)
            img.save(LOGO_FILE)
            st.success("校徽更換成功！")
            st.rerun()

    with st.expander("👨‍🎓 學生名冊管理", expanded=False):
        raw_list = st.text_area("貼上名單 (換行或逗號隔開)")
        if st.button("確認更新名冊"):
            final_list = [n.strip() for n in raw_list.replace("\n", ",").split(",") if n.strip()]
            if final_list:
                pd.DataFrame({"姓名": final_list}).to_csv(STUDENT_LIST_FILE, index=False, encoding='utf-8-sig')
                st.success(f"已成功建立 {len(final_list)} 位學生！")
                st.rerun()
