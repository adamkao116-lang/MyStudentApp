import streamlit as st
import pandas as pd
from datetime import datetime
import os
from PIL import Image

# ==========================================
# 1. 系統路徑與參數設定
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
# 2. 核心資料讀取與修復邏輯 (防止雲端報錯關鍵)
# ==========================================
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            # 讀取時指定編碼，避免 Excel 亂碼
            df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
            # [重要修復] errors='coerce' 會將壞掉的日期轉為空值，避免 ValueError 當機
            df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
            # 只保留正確的日期，自動踢掉壞資料
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

# 初始化載入
records_df = load_data()
students = sorted(load_master_list())
class_name = load_class_name()

# ==========================================
# 3. 網頁佈局 (校徽與標題並排)
# ==========================================
st.set_page_config(page_title=f"{class_name} 點名系統", layout="wide", page_icon="🏫")

# 建立圖文並行的標題列
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
        st.info("💡 提示：預設皆為『準時』，您只需修改特殊狀況。")
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
                
                # 存檔至 CSV (Excel 友善格式)
                new_df = pd.concat([records_df, pd.DataFrame(new_entries)], ignore_index=True)
                new_df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                st.success(f"✅ {c_date} 點名資料已成功儲存！")
                st.rerun()

# --- 分頁二：報表中心 ---
with tab2:
    st.header("🔍 資料查詢與導出")
    rtype = st.radio("呈現模式", ["全班月度統計表", "全班單日檢視", "個人區間追蹤"], horizontal=True)
    
    if rtype == "全班月度統計表":
        cm1, cm2 = st.columns(2)
        s_year = cm1.selectbox("年份", [2025, 2026, 2027], index=1)
        s_month = cm2.selectbox("月份", range(1, 13), index