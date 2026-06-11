import streamlit as st
import pandas as pd
# 若要使用 Google Sheets API，請在上方 import，這裡先移除以免報錯

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

all_df = load_data()

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

    # 定義分頁
    tab1, tab2, tab3, tab4 = st.tabs(["✅ 點名", "🎲 抽籤/發言", "👥 分組", "💰 繳費"])

    with tab1:
        st.subheader(f"{selected_class} 點名")
        for _, row in df_class.iterrows():
            name = row['姓名']
            st.session_state[f'attendance_{selected_class}'][name] = st.checkbox(get_display_name(row), value=st.session_state[f'attendance_{selected_class}'][name])

    present_students = [name for name, present in st.session_state[f'attendance_{selected_class}'].items() if present]

    with tab2:
        st.subheader("隨機抽籤與發言統計")
        if st.button("🎲 隨機抽籤"):
            if present_students:
                winner = pd.Series(present_students).sample(1).iloc[0]
                st.session_state[f'scores_{selected_class}'][winner] += 1
                st.rerun()
        
        for name in present_students:
            col1, col2 = st.columns([3, 1])
            score = st.session_state[f'scores_{selected_class}'].get(name, 0)
            col1.write(f"{name} (累積：{score} 次)")
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
        
        paid_count = sum(st.session_state[f'payment_{selected_class}'].values())
        st.info(f"💰 繳費統計：共 {len(df_class)} 人，已繳 {paid_count} 人，未繳 {len(df_class) - paid_count} 人")
        
        # 匯出紀錄按鈕
        if st.button("💾 匯出目前紀錄"):
            export_df = pd.DataFrame({
                "姓名": list(st.session_state[f'payment_{selected_class}'].keys()),
                "已繳費": list(st.session_state[f'payment_{selected_class}'].values())
            })
            csv = export_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 下載 CSV", csv, "records.csv", "text/csv")
