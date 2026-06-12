import streamlit as st
import pandas as pd
import datetime
import requests

# --- 設定頁面 ---
st.set_page_config(layout="wide")
st.title("🍎 班級經營系統")

# --- 資料讀取函式 ---
@st.cache_data(ttl=600)
def load_csv(url):
    try:
        return pd.read_csv(url)
    except:
        return pd.DataFrame()

# 填入你的 CSV 網址
ALL_STUDENTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=0&single=true&output=csv"
HISTORY_URL = "填入你的總資料庫CSV網址"

all_df = load_csv(ALL_STUDENTS_URL)
history_df = load_csv(HISTORY_URL)

# --- 主邏輯 ---
if all_df.empty:
    st.error("⚠️ 無法讀取學生名單！請檢查第一個 Google Sheet 是否已發布。")
else:
    selected_class = st.sidebar.selectbox("請選擇班級", all_df["班級"].unique())
    df_class = all_df[all_df["班級"] == selected_class].copy()
    
    # 初始化 session_state
    def get_display_name(row):
        return f"{int(row['班級'])}-{int(row['座號'])}-{row['姓名']}"

    if f'attendance_{selected_class}' not in st.session_state:
        st.session_state[f'attendance_{selected_class}'] = {name: True for name in df_class["姓名"]}
        st.session_state[f'scores_{selected_class}'] = {name: 0 for name in df_class["姓名"]}
        st.session_state[f'payment_{selected_class}'] = {name: False for name in df_class["姓名"]}
        st.session_state[f'last_winner_{selected_class}'] = None

    tab1, tab2, tab3, tab4 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組", "💰 繳費"])
    
    # ... (這裡放入你原本的 tab1~tab3 程式碼) ...

    with tab4:
        st.subheader(f"{selected_class} 繳費管理")
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'payment_{selected_class}'][name] = st.checkbox(
                f"{int(row['班級'])}-{int(row['座號'])}-{row['姓名']}", 
                value=st.session_state[f'payment_{selected_class}'][name], key=f"pay_{name}"
            )
        
        if st.button("💾 儲存今日紀錄至總資料庫"):
            WEB_APP_URL = "https://script.google.com/macros/s/AKfycbz6v1LiJXiMQobPT-knkNUBSZ4ut4OwUbcKpzoFiSWKMaj2s8dqsKcmYeuJP8_bVY8UYw/exec"
            with st.spinner("正在寫入..."):
                for name in df_class["姓名"]:
                    row = df_class[df_class['姓名'] == name].iloc[0]
                    payload = {
                        "日期": datetime.date.today().strftime("%Y/%m/%d"),
                        "班級": int(row['班級']),
                        "座號": int(row['座號']),
                        "姓名": row['姓名'],
                        "出席狀態": "出席" if st.session_state[f'attendance_{selected_class}'][name] else "缺席",
                        "繳費狀態": "已繳" if st.session_state[f'payment_{selected_class}'][name] else "未繳",
                        "發言次數": st.session_state[f'scores_{selected_class}'][name]
                    }
                    requests.post(WEB_APP_URL, json=payload)
                st.success("✅ 同步完成！")

    # --- 歷史統計 ---
    st.divider()
    st.subheader("📊 20 週歷史紀錄與統計")
    if not history_df.empty:
        # 請確保這裡的欄位名稱跟你的 Google Sheet 標題完全一致
        class_history = history_df[history_df["班級"] == int(selected_class)]
        st.dataframe(class_history)
        # (這裡放入你的統計計算邏輯)
