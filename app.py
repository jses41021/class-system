import streamlit as st
import pandas as pd
import datetime

# --- 設定頁面 ---
st.set_page_config(layout="wide")
st.title("🍎 班級經營系統")

# --- 載入基礎資料 ---
@st.cache_data(ttl=600)
def load_data():
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=0&single=true&output=csv"
    try: return pd.read_csv(csv_url)
    except: return pd.DataFrame()

# --- 新增：讀取歷史紀錄 (請將下方網址改為您的歷史總表 CSV 連結) ---
@st.cache_data(ttl=600)
def load_history():
    history_url = "您的歷史紀錄表_發布至網路的CSV連結"
    try: return pd.read_csv(history_url)
    except: return pd.DataFrame()

all_df = load_data()
history_df = load_history()

if not all_df.empty:
    selected_class = st.sidebar.selectbox("請選擇班級", all_df["班級"].unique())
    df_class = all_df[all_df["班級"] == selected_class].copy()
    
    def get_display_name(row):
        return f"{int(row['班級'])}-{int(row['座號'])}-{row['姓名']}"

    # 初始化 session_state
    if f'attendance_{selected_class}' not in st.session_state:
        st.session_state[f'attendance_{selected_class}'] = {name: True for name in df_class["姓名"]}
    if f'scores_{selected_class}' not in st.session_state:
        st.session_state[f'scores_{selected_class}'] = {name: 0 for name in df_class["姓名"]}
    if f'payment_{selected_class}' not in st.session_state:
        st.session_state[f'payment_{selected_class}'] = {name: False for name in df_class["姓名"]}

    tab1, tab2, tab3, tab4 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組", "💰 繳費與紀錄"])

    with tab1:
        # (您的點名邏輯維持不變)
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'attendance_{selected_class}'][name] = st.checkbox(get_display_name(row), value=st.session_state[f'attendance_{selected_class}'][name])

    with tab2:
        # (您的抽籤邏輯維持不變)
        pass 

    with tab3:
        # (您的分組邏輯維持不變)
        pass

    with tab4:
        st.subheader(f"{selected_class} 繳費管理")
        # 顯示勾選框
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'payment_{selected_class}'][name] = st.checkbox(f"{name}", value=st.session_state[f'payment_{selected_class}'][name], key=f"pay_{name}")
        
        # 匯出本週按鈕
        if st.button("💾 匯出本週紀錄 (CSV)"):
            # ... (匯出邏輯維持不變) ...
            pass
        
        st.divider()
        st.subheader("📊 20 週歷史紀錄總覽")
        if not history_df.empty:
            st.dataframe(history_df)
        else:
            st.info("尚未載入歷史紀錄，請確認總表連結是否正確。")
