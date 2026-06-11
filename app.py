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
    try:
        return pd.read_csv(csv_url)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_history():
    # 請確保這是一個有效的公開 CSV 連結
    history_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=123456&single=true&output=csv"
    try:
        return pd.read_csv(history_url)
    except:
        return pd.DataFrame()

all_df = load_data()
history_df = load_history()

if not all_df.empty:
    selected_class = st.sidebar.selectbox("請選擇班級", all_df["班級"].unique())
    df_class = all_df[all_df["班級"] == selected_class].copy()
    
    # 初始化 session
    if f'attendance_{selected_class}' not in st.session_state:
        st.session_state[f'attendance_{selected_class}'] = {name: True for name in df_class["姓名"]}
    if f'scores_{selected_class}' not in st.session_state:
        st.session_state[f'scores_{selected_class}'] = {name: 0 for name in df_class["姓名"]}
    if f'payment_{selected_class}' not in st.session_state:
        st.session_state[f'payment_{selected_class}'] = {name: False for name in df_class["姓名"]}

    tab1, tab2, tab3, tab4 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組", "💰 繳費與紀錄"])

    with tab1:
        st.subheader("點名")
        for _, row in df_class.iterrows():
            name = row['姓名']
            label = f"{int(row['班級'])}-{int(row['座號'])}-{name}"
            st.session_state[f'attendance_{selected_class}'][name] = st.checkbox(label, value=st.session_state[f'attendance_{selected_class}'][name])

    with tab2:
        st.subheader("發言統計")
        # (這裡省略部分抽籤邏輯以精簡)
        for name in df_class["姓名"]:
            col1, col2 = st.columns([3, 1])
            col1.write(f"{name}: {st.session_state[f'scores_{selected_class}'].get(name, 0)} 次")
            if col2.button("加分", key=f"btn_{name}"):
                st.session_state[f'scores_{selected_class}'][name] += 1
                st.rerun()

    with tab3:
        st.subheader("隨機分組")
        # (這裡省略分組邏輯)

    with tab4:
        st.subheader(f"{selected_class} 繳費管理")
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'payment_{selected_class}'][name] = st.checkbox(f"{name}", value=st.session_state[f'payment_{selected_class}'][name], key=f"pay_{name}")
        
        st.divider()
        st.subheader("📊 歷史紀錄總覽")
        if not history_df.empty:
            st.dataframe(history_df)
        else:
            st.write("目前無歷史紀錄。請確認 CSV 連結是否正確。")

        if st.button("💾 下載本週紀錄"):
            # (這裡放原本的 CSV 下載邏輯)
            pass
