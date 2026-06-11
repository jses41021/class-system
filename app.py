import streamlit as st
import pandas as pd
import requests

# 建議將 CSV 網址直接填入下方 (請替換為您正確的網址)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?output=csv"
GAS_URL = "https://script.google.com/macros/s/AKfycbzR2K6nyJvCtq1JrUsAQJ1h8NjzuJU9erW3tpKX1G41GcH1xx6mLVqyU8F_8iQOqhTi8w/exec"

st.set_page_config(layout="wide")
st.title("🍎 班級經營系統")

@st.cache_data(ttl=600)
def load_data():
    try:
        return pd.read_csv(CSV_URL)
    except Exception as e:
        st.error(f"讀取名單失敗，請確認 CSV 網址是否正確。錯誤: {e}")
        return pd.DataFrame()

all_df = load_data()
if not all_df.empty:
    selected_class = st.sidebar.selectbox("請選擇班級", all_df["班級"].unique())
    df_class = all_df[all_df["班級"] == selected_class].copy()

    # 初始化狀態 (存於 session_state)
    if 'scores' not in st.session_state:
        st.session_state['scores'] = {name: 0 for name in df_class["姓名"]}

    tab1, tab2, tab3, tab4 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組", "💰 繳費"])

    with tab1:
        st.subheader(f"{selected_class} 點名")
        df_class["出席"] = True
        edited = st.data_editor(df_class[["座號", "姓名", "出席"]], hide_index=True)
        if st.button("儲存點名"):
            st.success("點名紀錄已暫存")

    with tab2:
        st.subheader("抽籤與發言")
        for idx, row in df_class.iterrows():
            col1, col2 = st.columns([4, 1])
            name = row['姓名']
            score = st.session_state['scores'].get(name, 0)
            col1.write(f"{row['座號']}號 {name} (累積：{score})")
            if col2.button("加分", key=f"btn_{name}"):
                st.session_state['scores'][name] += 1
                st.rerun()

        if st.button("🎲 隨機抽籤"):
            winner = df_class.sample(1).iloc[0]
            st.session_state['scores'][winner['姓名']] += 1
            st.success(f"抽中：{winner['座號']}號 {winner['姓名']}")
            st.rerun()

    with tab3:
        st.subheader("一鍵隨機分組")
        cols = st.columns(5)
        for n in [3, 4, 5, 6, 8]:
            if cols[[3, 4, 5, 6, 8].index(n)].button(f"{n}組"):
                shuffled = df_class["姓名"].sample(frac=1).tolist()
                for i, group in enumerate([shuffled[i::n] for i in range(n)]):
                    st.write(f"第{i+1}組: {', '.join(group)}")

    with tab4:
        st.subheader("繳費管理")
        df_class["繳費"] = False
        st.data_editor(df_class[["座號", "姓名", "繳費"]], hide_index=True)
