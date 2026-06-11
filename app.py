import streamlit as st
import pandas as pd
import random

# --- 1. 資料處理 (自動載入您的 CSV 名單) ---
@st.cache_data(ttl=600)
def load_students():
    # 請將此網址換成您 Google Sheet 發佈的 CSV 網址
    url = "YOUR_CSV_URL_HERE" 
    df = pd.read_csv(url)
    return df

st.set_page_config(layout="wide")
st.title("🍎 班級經營系統")

# 載入全部名單
all_df = load_students()
classes = all_df["班級"].unique()

# --- 2. 班級分頁與數據同步 ---
# 使用 selectbox 選擇班級，系統會自動只顯示該班級的資料
selected_class = st.sidebar.selectbox("請選擇班級", classes)
df_class = all_df[all_df["班級"] == selected_class].copy()

# 在 session_state 中追蹤「加分/發言次數」
if f'scores_{selected_class}' not in st.session_state:
    st.session_state[f'scores_{selected_class}'] = {name: 0 for name in df_class["姓名"]}

# --- 3. 功能分頁 ---
tab1, tab2, tab3, tab4 = st.tabs(["✅ 點名", "🎲 抽籤/發言統計", "👥 隨機分組", "💰 繳費"])

# 點名頁面
with tab1:
    st.subheader(f"{selected_class} 點名")
    df_class["出席"] = True
    edited = st.data_editor(df_class[["座號", "姓名", "出席"]], hide_index=True)
    if st.button("儲存點名"):
        st.success("已儲存！")

# 抽籤與發言計分頁面
with tab2:
    st.subheader("抽籤與發言統計")
    # 顯示學生列表與次數
    for idx, row in df_class.iterrows():
        col1, col2 = st.columns([3, 1])
        name = row['姓名']
        score = st.session_state[f'scores_{selected_class}'][name]
        col1.write(f"{row['座號']}號 {name} (累積：{score} 次)")
        if col2.button("加分/計次", key=f"btn_{name}"):
            st.session_state[f'scores_{selected_class}'][name] += 1
            st.rerun()

    if st.button("🎲 隨機抽籤 (自動計分)"):
        # 根據次數加權機率
        weights = [1 / (st.session_state[f'scores_{selected_class}'][name] + 1) for name in df_class["姓名"]]
        winner = df_class.sample(1, weights=weights).iloc[0]
        st.session_state[f'scores_{selected_class}'][winner['姓名']] += 1
        st.balloons()
        st.subheader(f"抽中：{winner['座號']}號 {winner['姓名']}")
        st.rerun()

# 分組頁面
with tab3:
    st.subheader("一鍵隨機分組")
    cols = st.columns(5)
    nums = [3, 4, 5, 6, 8]
    for i, n in enumerate(nums):
        if cols[i].button(f"{n} 組"):
            shuffled = df_class["姓名"].sample(frac=1).tolist()
            groups = [shuffled[i::n] for i in range(n)]
            for g_idx, group in enumerate(groups):
                st.write(f"第 {g_idx+1} 組: {', '.join(group)}")
