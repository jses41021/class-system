import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🍎 班級經營系統")

# 假設這是您的 CSV 資料，您部署時請確認 load_data 函式正確指向您的 CSV
@st.cache_data(ttl=600)
def load_data():
    # 這裡請替換為您正確的 CSV 發佈連結
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8_2gDvKiTieAleMNeHdN1owBrEtkhhWBrg3Bpl3b8CzURHgOBouqPJ-_-LTbP8ZXJyPywXlnTKkKj/pub?gid=0&single=true&output=csv" 
    return pd.read_csv(url)

all_df = load_data()
if not all_df.empty:
    selected_class = st.sidebar.selectbox("請選擇班級", all_df["班級"].unique())
    df_class = all_df[all_df["班級"] == selected_class].copy()
    
    # --- 初始化 session_state ---
    if f'scores_{selected_class}' not in st.session_state:
        st.session_state[f'scores_{selected_class}'] = {name: 0 for name in df_class["姓名"]}
    
    # 初始預設全體出席
    if f'attendance_{selected_class}' not in st.session_state:
        st.session_state[f'attendance_{selected_class}'] = {name: True for name in df_class["姓名"]}

    tab1, tab2, tab3 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組"])

    with tab1:
        st.subheader(f"{selected_class} 點名 (打勾代表出席)")
        for name in df_class["姓名"]:
            st.session_state[f'attendance_{selected_class}'][name] = st.checkbox(name, value=st.session_state[f'attendance_{selected_class}'][name])

    # --- 篩選出席學生 ---
    present_students = [name for name, present in st.session_state[f'attendance_{selected_class}'].items() if present]

    with tab2:
        st.subheader("隨機抽籤與發言統計")
        # 抽籤按鈕移到上方
        if st.button("🎲 隨機抽籤 (僅限出席者)"):
            if present_students:
                winner = pd.Series(present_students).sample(1).iloc[0]
                st.session_state[f'scores_{selected_class}'][winner] += 1
                st.balloons()
                st.success(f"🎉 抽中：{winner}")
            else:
                st.warning("沒有學生出席！")
        
        st.write("---")
        # 主動加分清單
        for name in present_students:
            col1, col2 = st.columns([3, 1])
            score = st.session_state[f'scores_{selected_class}'][name]
            col1.write(f"{name} (累積：{score} 次)")
            if col2.button("加分", key=f"btn_{name}"):
                st.session_state[f'scores_{selected_class}'][name] += 1
                st.rerun()

    with tab3:
        st.subheader("隨機分組 (僅限出席者)")
        cols = st.columns(5)
        nums = [3, 4, 5, 6, 8]
        for i, n in enumerate(nums):
            if cols[i].button(f"{n} 組"):
                if len(present_students) >= n:
                    random_list = pd.Series(present_students).sample(frac=1).tolist()
                    groups = [random_list[i::n] for i in range(n)]
                    for g_idx, group in enumerate(groups):
                        st.write(f"第 {g_idx+1} 組: {', '.join(group)}")
                else:
                    st.error("出席人數不足以分組")
