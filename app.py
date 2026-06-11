import streamlit as st
import pandas as pd
import datetime

# --- 1. 設定頁面 ---
st.set_page_config(layout="wide")
st.title("🍎 班級經營系統")

# --- 2. 載入資料 (請保持不變) ---
@st.cache_data(ttl=600)
def load_data():
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=0&single=true&output=csv"
    try: return pd.read_csv(csv_url)
    except: return pd.DataFrame()

# --- 3. 新增：讀取歷史紀錄 (這裡是儲存 20 週紀錄的關鍵) ---
@st.cache_data(ttl=600)
def load_history():
    # 當您在 Google Sheet 發布 CSV 後，將連結貼在這裡
    history_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVhobz_uXg7PcjS9BJh0kKh2KosiFnPLAyQq8hiGVPxuQIwCrJVU6pcyYLOukIY2hQIB2e8qXROmBu/pub?output=csv" 
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

    # --- 4. 分頁結構 (所有功能都在這) ---
    tab1, tab2, tab3, tab4 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組", "💰 繳費與紀錄"])

    with tab1:
        st.subheader(f"{selected_class} 點名")
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'attendance_{selected_class}'][name] = st.checkbox(get_display_name(row), value=st.session_state[f'attendance_{selected_class}'][name])

    present_students = [name for name, present in st.session_state[f'attendance_{selected_class}'].items() if present]

    with tab2:
        st.subheader("隨機抽籤與發言統計")
        if st.button("🎲 抽籤"):
            if present_students:
                winner = pd.Series(present_students).sample(1).iloc[0]
                st.session_state[f'scores_{selected_class}'][winner] += 1
                st.session_state[f'last_winner_{selected_class}'] = winner
                st.rerun()
        for name in present_students:
            col1, col2 = st.columns([3, 1])
            col1.write(f"{name} (累積：{st.session_state[f'scores_{selected_class}'].get(name, 0)} 次)")
            if col2.button("加分", key=f"btn_{name}"):
                st.session_state[f'scores_{selected_class}'][name] += 1
                st.rerun()

    with tab3:
        st.subheader("隨機分組")
        for n in [3, 4, 5, 6, 8]:
            if st.button(f"{n} 組"):
                if len(present_students) >= n:
                    random_list = pd.Series(present_students).sample(frac=1).tolist()
                    groups = [random_list[i::n] for i in range(n)]
                    for i, group in enumerate(groups):
                        st.write(f"第 {i+1} 組: {', '.join(group)}")

    with tab4:
        st.subheader(f"{selected_class} 繳費管理")
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'payment_{selected_class}'][name] = st.checkbox(get_display_name(row), value=st.session_state[f'payment_{selected_class}'][name], key=f"pay_{name}")
        
        if st.button("💾 匯出本週紀錄 (CSV)"):
            # 這裡執行您的匯出邏輯
            pass
            
        st.divider()
        st.subheader("📊 20 週歷史紀錄回顧")
        if not history_df.empty:
            st.dataframe(history_df)
        else:
            st.info("請設定歷史紀錄連結，即可在此查看 20 週累積數據。")
