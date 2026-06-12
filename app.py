import streamlit as st
import pandas as pd
import datetime
import requests

# --- 設定頁面 ---
st.set_page_config(layout="wide")
st.title("🍎 班級經營系統")

# --- 設定網址 ---
STUDENT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=0&single=true&output=csv"
HISTORY_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=2042566365&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        return pd.read_csv(url)
    except:
        return pd.DataFrame()

all_df = load_data(STUDENT_URL)
history_df = load_data(HISTORY_URL)

if all_df.empty:
    st.warning("⚠️ 學生名單讀取失敗！")
else:
    selected_class = st.sidebar.selectbox("請選擇班級", all_df["班級"].unique())
    df_class = all_df[all_df["班級"] == selected_class].copy()
    
    # 確保歷史資料有正確格式
    history_df['班級'] = pd.to_numeric(history_df['班級'], errors='coerce')
    class_history = history_df[history_df["班級"] == int(selected_class)].copy()

    # 初始化 session_state
    if f'attendance_{selected_class}' not in st.session_state:
        st.session_state[f'attendance_{selected_class}'] = {name: True for name in df_class["姓名"]}
        st.session_state[f'scores_{selected_class}'] = {name: 0 for name in df_class["姓名"]}
        st.session_state[f'payment_{selected_class}'] = {name: False for name in df_class["姓名"]}
        st.session_state[f'last_winner_{selected_class}'] = None

    tab1, tab2, tab3, tab4 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組", "💰 繳費"])

    with tab1:
        st.subheader("點名 (勾選代表出席)")
        for _, row in df_class.iterrows():
            name = row['姓名']
            # 修改顯示格式
            display_name = f"{int(row['班級'])}-{int(row['座號'])}-{name}"
            st.session_state[f'attendance_{selected_class}'][name] = st.checkbox(
                display_name, value=st.session_state[f'attendance_{selected_class}'][name]
            )

    with tab2:
        st.subheader("隨機抽籤")
        if st.button("🎲 抽籤 (僅限出席者)"):
            if present_students:
                winner = pd.Series(present_students).sample(1).iloc[0]
                st.session_state[f'last_winner_{selected_class}'] = winner
                st.session_state[f'scores_{selected_class}'][winner] += 1
        
        if st.session_state[f'last_winner_{selected_class}']:
            winner = st.session_state[f'last_winner_{selected_class}']
            # 找到獲勝者的班級座號
            winner_row = df_class[df_class['姓名'] == winner].iloc[0]
            st.success(f"🎉 剛剛抽中：{int(winner_row['班級'])}-{int(winner_row['座號'])}-{winner}")

        for name in present_students:
            row = df_class[df_class['姓名'] == name].iloc[0]
            display_name = f"{int(row['班級'])}-{int(row['座號'])}-{name}"
    with tab3:
        st.subheader("隨機分組")
        group_n = st.selectbox("組數", [3, 4, 5, 6, 8])
        if st.button("開始分組"):
            shuffled = pd.Series(present_students).sample(frac=1).tolist()
            groups = [shuffled[i::group_n] for i in range(group_n)]
            for i, g in enumerate(groups):
                st.write(f"第 {i+1} 組: {', '.join(g)}")

    with tab4:
        st.subheader("繳費管理")
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'payment_{selected_class}'][name] = st.checkbox(f"{name}", value=st.session_state[f'payment_{selected_class}'][name], key=f"pay_{name}")
        
        if st.button("💾 儲存今日紀錄"):
        with st.spinner("正在處理中..."):
            all_data = []
            for name in df_class["姓名"]:
                row = df_class[df_class['姓名'] == name].iloc[0]
                # 這裡假設你有一個變數儲存了當前的分組結果
                # 若無，可設為"無"或從 session_state 讀取
                group_info = st.session_state.get(f'group_{selected_class}', "無") 
                
                data = {
                    "日期": datetime.date.today().strftime("%Y/%m/%d"),
                    "班級": int(row['班級']),
                    "座號": int(row['座號']),
                    "姓名": name,
                    "出席狀態": "出席" if st.session_state[f'attendance_{selected_class}'][name] else "缺席",
                    "繳費狀態": "已繳" if st.session_state[f'payment_{selected_class}'][name] else "未繳",
                    "發言次數": st.session_state[f'scores_{selected_class}'][name],
                    "中籤次數": 1 if name == st.session_state.get(f'last_winner_{selected_class}') else 0,
                    "分組": group_info
                }
                all_data.append(data)
            
            # 使用 requests.post 發送
            try:
                requests.post(WEB_APP_URL, json=all_data, timeout=10)
                st.success("✅ 同步完成！")
            except Exception as e:
                st.error(f"儲存失敗: {e}")

    # --- 歷史統計 ---
    st.divider()
    st.subheader("📊 個人累積統計表")
    if not class_history.empty:
        stats_df = class_history.copy()
        for col in ['發言次數', '中籤次數', '分組']:
            stats_df[col] = stats_df[col] if col in stats_df.columns else 0
            if col != '分組': stats_df[col] = pd.to_numeric(stats_df[col], errors='coerce').fillna(0)
        
        stats = stats_df.groupby(['座號', '姓名']).agg({
            '出席狀態': lambda x: (x == '出席').sum(),
            '發言次數': 'sum', '中籤次數': 'sum', '分組': 'last'
        }).reset_index()
        st.dataframe(stats, use_container_width=True)
