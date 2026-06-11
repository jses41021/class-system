import streamlit as st
import pandas as pd
import datetime

# --- 設定頁面 ---
st.set_page_config(layout="wide")
st.title("🍎 班級經營系統")

# --- 載入資料 ---
@st.cache_data(ttl=600)
def load_data():
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=0&single=true&output=csv"
    try: return pd.read_csv(csv_url)
    except: return pd.DataFrame()

# --- 新增：讀取 20 週歷史總表 ---
@st.cache_data(ttl=600)
def load_history():
    # 這裡請替換成您那份「歷史紀錄總表」的 CSV 發布連結
    history_url = "https://docs.google.com/spreadsheets/d/e/YOUR_CSV_LINK_HERE/pub?gid=0&single=true&output=csv"
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
    if f'last_winner_{selected_class}' not in st.session_state:
        st.session_state[f'last_winner_{selected_class}'] = None

    tab1, tab2, tab3, tab4 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組", "💰 繳費與紀錄"])

    # [tab1, tab2, tab3 邏輯維持不變，放在此處]
    # (為節省空間，此處省略，請使用您原始程式碼中對應的內容)
    # ... (點名、抽籤、分組邏輯) ...

    with tab4:
        st.subheader(f"{selected_class} 繳費管理")
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'payment_{selected_class}'][name] = st.checkbox(
                get_display_name(row), value=st.session_state[f'payment_{selected_class}'][name], key=f"pay_{name}"
            )
        
        if st.button("💾 匯出本週紀錄 (CSV)"):
            # ... (您的匯出邏輯) ...
            pass
        
        st.divider()
        st.subheader("📊 20 週歷史紀錄回顧")
        if not history_df.empty:
            st.dataframe(history_df, use_container_width=True)
        else:
            st.warning("尚未讀取到歷史紀錄。請確認 `history_url` 是否已設定為您的歷史總表連結。")
